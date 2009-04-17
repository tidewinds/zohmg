package fm.last.darling;

import java.io.DataInput;
import java.io.IOException;
import java.io.InputStream;
import java.io.UnsupportedEncodingException;
import java.nio.charset.CharacterCodingException;
import java.util.Map;
import java.util.Set;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.io.BatchUpdate;
import org.apache.hadoop.hbase.io.ImmutableBytesWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.streaming.PipeMapRed;
import org.apache.hadoop.streaming.StreamKeyValUtil;
import org.apache.hadoop.streaming.io.OutputReader;
import org.apache.hadoop.util.LineReader;
import org.apache.hadoop.util.StringUtils;
import org.apache.hadoop.util.UTF8ByteArrayUtils;
import org.apache.noggit.ObjectBuilder;

/**
 * OutputReader that transforms the client's output HBasey BatchUpdates.
 * 
 */
public class HBaseOutputReader extends OutputReader<ImmutableBytesWritable, BatchUpdate> {

	private ImmutableBytesWritable rowkey;
	private BatchUpdate batchupdate;

	// save the last seen line of output as Text
	// and the bytes, so that getLastOutput can recreate it as a string.
	private Text line;
	private byte[] bytes;

	private DataInput datainput;
	private Configuration conf;
	private int numKeyFields;
	private byte[] separator;

	private LineReader lineReader;


	@Override
	public void initialize(PipeMapRed pipeMapRed) throws IOException {
		super.initialize(pipeMapRed);

		rowkey = new ImmutableBytesWritable();
		batchupdate = new BatchUpdate();
		line = new Text();
		
		datainput = pipeMapRed.getClientInput();
		conf      = pipeMapRed.getConfiguration();
		numKeyFields = pipeMapRed.getNumOfKeyFields();
		separator    = pipeMapRed.getFieldSeparator();
		
		/*
		System.err.println("HBaseOutputReader");
		System.err.println("numkeyfields: " + new Integer(numKeyFields));
		System.err.println("separator: " + separator);
		*/
		
		lineReader = new LineReader((InputStream) datainput, conf);
	}

	@Override
	public boolean readKeyValue() throws IOException {
		if (lineReader.readLine(line) <= 0)
			return false;	
		// populate member variables rowkey and batchupdate
		bytes = line.getBytes();
		interpretKeyandValue(bytes, line.getLength());
		line.clear();
		return true;
	}

	// split a UTF-8 line into key and value
	// lifted from from org.apache.hadoop.streaming.io.TextOutputReader
	private void interpretKeyandValue(byte[] line, int length) throws IOException {
		// Need to find numKeyFields separators
		int pos = UTF8ByteArrayUtils.findBytes(line, 0, length, separator);
		for(int k=1; k<numKeyFields && pos!=-1; k++) {
			pos = UTF8ByteArrayUtils.findBytes(line, pos + separator.length, 
					length, separator);
		}

		Text k = new Text();
		Text v = new Text();
		try {
			if (pos == -1) {
				k.set(line, 0, length);
				v.set("");
			} else {
				StreamKeyValUtil.splitKeyVal(line, 0, length, k, v, pos,
						separator.length);
			}
		} catch (CharacterCodingException e) {
			throw new IOException(StringUtils.stringifyException(e));
		}

		// and now, los interpretaziones.

		// FIXME: ouch, that's ugly!
		String rk    = k.toString().substring(1, k.toString().length() - 1);

		rowkey = new ImmutableBytesWritable(rk.getBytes());
		batchupdate = new BatchUpdate(rk.getBytes());
	
		/*
		System.err.println("HBaseOutputReader#interpretKeyandValue");
		System.err.println("k: " + k.toString());
		System.err.println("v: " + v.toString());
		System.err.println("rowkey: " + rk);
		*/
				
		String json = v.toString().substring(1, v.toString().length() - 1);
		Map<String, Map> payload;
		try {
			payload = (Map<String, Map>) ObjectBuilder.fromJSON(json); // the 'erased' type?
			System.err.println("payload: " + payload.getClass());
		} catch (Exception e) {
			System.err.println("fromJson: " + e.toString());
			return;
		}
		
		Set<Map.Entry<String, Map>> entries = payload.entrySet();
		for (Map.Entry<String, Map> entry : entries) {
			String cfq = entry.getKey();
			Map dict   = entry.getValue(); // unchecked.
			
			// expecting dict to carry 'value' and possibly 'timestamp'
			if (!dict.containsKey("value"))
				return; // no good.
			Object value = dict.get("value");
			
			Object ts = 0;
			if (dict.containsKey("timestamp"))
				ts = dict.get("timestamp");
			
			System.err.println("cfq: " + cfq + " has value " + value + " (and possibly timestamp: "+ts+").");
					
			batchupdate.put(cfq, value.toString().getBytes());
		}
	}


	@Override
	public ImmutableBytesWritable getCurrentKey() throws IOException {
		return rowkey;
	}

	@Override
	public BatchUpdate getCurrentValue() throws IOException {
		return batchupdate;
	}

	@Override
	public String getLastOutput() {
		try {
			return new String(bytes, "UTF-8");
		} catch (UnsupportedEncodingException e) {
			return "<undecodable>";
		}
	}

}