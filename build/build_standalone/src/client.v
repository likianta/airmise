import compress.szip // https://modules.vlang.io/compress.szip.html#zip_files
import json
import net.http
import os

struct Config {
	host 		  string
	frontend_port int
	backend_port  int
}

// v run src/client.v debug
// v src/client.v
fn main() {
	println(os.args)
	// os.args.len can be 1, 2 or 4.
	if os.args.len > 1 {
		assert os.args[1] == 'debug'
	}
	debug := if os.args.len > 1 { true } else { false }

	root := detect_airclient(debug)!
	os.chdir(root)!

	println('execute python script')
	// os.execvp('python/python.exe', ['src/client.py', '-h'])!
	conf := get_config(debug)!
	println(conf)
	os.execvp(
		'python/python.exe',
		[
			'src/client.py', conf.host,
			'-f', conf.frontend_port.str(),
			'-b', conf.backend_port.str()
		]
	)!
}

fn detect_airclient(debug bool) !string {
	mut airclient_root := ''
	if debug {
		airclient_root = 'C:/Likianta/apps/airmise/airclient_standalone'
		if !os.exists(airclient_root) {
			println('airclient not found, now download the binary from server')
			x := download('C:/Likianta/apps/airmise', debug)!
			assert airclient_root == x
		}
	} else {
		airclient_root = os.environ()['AIRCLIENT_ROOT']
		if airclient_root == '' {
			println('airclient not found, now download the binary from server')
			airmise_root := string_interp('{}/airmise', [
				os.environ()['APPDATA'].replace('\\', '/')
			])
			os.mkdir(airmise_root)!
			airclient_root = download(airmise_root, debug)!
			println([airmise_root, airclient_root])
			// assert airclient_root.startswith(airmise_root)
			// TODO: set environment
		}
	}
	return airclient_root
}

fn download(root string, debug bool) !string {
	host := if debug { 'localhost' } else { '47.102.108.149' }
	url := 'http://${host}:2184/airclient_standalone.zip'
	zip := '${root}/airclient_standalone.zip'
	dir := '${root}/airclient_standalone'
	http.download_file(url, zip)!
	os.mkdir(dir)!
	// szip.extract_zip_to_dir(zip, dir)!
	szip.extract_zip_to_dir(zip, root)!
	return dir
}

fn get_config(debug bool) !Config {
	if os.args.len == 4 {
		return Config{
			if debug {'localhost'} else {'47.102.108.149'},
			os.args[2].int(),
			os.args[3].int()
		}
	} else {
		return json.decode(
			Metadata,
			$embed_file('../build/client_config.yaml').to_string()
		)!
	}
}

fn string_interp(template string, placeholders []string) string {
	mut out := template
	for text in placeholders {
		out = out.replace_once('{}', text)
	}
	return out
}
