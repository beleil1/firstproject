import pyclamd


def scan_file_for_virus(file_content: bytes) -> bool:
    try:
        cd = pyclamd.ClamdUnixSocket()
        scan_result = cd.scan_stream(file_content)
        if scan_result[file_name] == 'OK':
            return False
        else:
            return True
    except pyclamd.ConnectionError:
        print('Could not connect to clamd server!')
        return False
