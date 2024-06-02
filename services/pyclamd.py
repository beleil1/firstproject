import pyclamd


def scan_file_for_virus(file_content: bytes) -> bool:
    try:
        cd = pyclamd.ClamdUnixSocket()
        scan_result = cd.scan_stream(file_content)
        if scan_result[file_name] == 'OK':
            return False  # فایل تمیز است
        else:
            return True  # فایل حاوی ویروس است
    except pyclamd.ConnectionError:
        print('Could not connect to clamd server!')
        return False  # فایل تمیز است
