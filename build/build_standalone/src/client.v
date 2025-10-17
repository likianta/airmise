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
// v run src/client.v debug -h
// v run src/client.v
fn main() {
	println(os.args)
	debug := if os.args.len > 1 { os.args[1] == 'debug' } else { false }
	// debug := (
	// 	if os.args.len > 1 { true }
	// 	else { if os.args[1] == 'debug' { true } else { false } }
	// )

	root := detect_airclient(debug)!
	os.chdir(root)!

	println('execute python script')
	if os.args[os.args.len - 1] == '-h' {
		os.execvp('python/python.exe', ['src/client.py', '-h'])!
	} else {
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
		airclient_root = os.getenv('AIRCLIENT_ROOT')
		if airclient_root == '' {
			println('airclient not found, now download the binary from server')
			parent_folder := string_interp('{}/airmise', [
				os.environ()['APPDATA'].replace('\\', '/')
			])
			os.mkdir(parent_folder)!
			airclient_root = download(parent_folder, debug)!
			println([parent_folder, airclient_root])
			// assert airclient_root.startswith(parent_folder)
			os.execute_or_panic('setx AIRCLIENT_ROOT "${airclient_root}"')
		}
	}
	return airclient_root
}

fn download(root string, debug bool) !string {
	host := if debug { 'localhost' } else { '47.102.108.149' }
	url := 'http://${host}:2143/airclient_standalone.zip'
	//	server side should make sure dufs & bore are running at port 2143.
	zip := '${root}/airclient_standalone.zip'
	dir := '${root}/airclient_standalone'
	http.download_file(url, zip)!
	os.mkdir(dir)!
	// szip.extract_zip_to_dir(zip, dir)!
	szip.extract_zip_to_dir(zip, root)!
	return dir
}

fn get_config(debug bool) !Config {
	// if debug mode, try to get config from os.args; else from embed file.
	if debug {
		if os.args.len == 2 {
			return Config{'localhost', 3001, 3002}
		}
		else if os.args.len == 3 {
			return Config{os.args[2], 3001, 3002}
		}
		else if os.args.len == 4 {
			return Config{'localhost', os.args[2].int(), os.args[3].int()}
		}
		else if os.args.len == 5 {
			return Config{os.args[2], os.args[3].int(), os.args[4].int()}
		}
		else {
			panic(os.args)
		}
	} else {
		return json.decode(
			Config,
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
