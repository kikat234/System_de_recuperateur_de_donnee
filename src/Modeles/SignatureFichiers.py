FILE_SIGNATURES = {
    'PDF': {'header': b'%PDF', 'footer': b'%%EOF', 'ext': '.pdf', 'min_size': 1024},
    'PNG': {'header': b'\x89PNG\r\n\x1a\n', 'footer': b'IEND\xae B`\x82', 'ext': '.png', 'min_size': 512},
    'JPEG': {'header': b'\xff\xd8\xff\xe0', 'footer': b'\xff\xd9', 'ext': '.jpg', 'min_size': 512},  # Signature plus précise
    'JPEG_ALT': {'header': b'\xff\xd8\xff\xe1', 'footer': b'\xff\xd9', 'ext': '.jpg', 'min_size': 512},  # EXIF
    'ZIP': {'header': b'PK\x03\x04', 'footer': b'PK\x05\x06', 'ext': '.zip', 'min_size': 1024},
    'DOCX': {'header': b'PK\x03\x04\x14\x00\x06\x00', 'footer': None, 'ext': '.docx', 'min_size': 2048},  # Plus spécifique
    'XLSX': {'header': b'PK\x03\x04\x14\x00\x06\x00', 'footer': None, 'ext': '.xlsx', 'min_size': 2048},
    'GIF': {'header': b'GIF89a', 'footer': b'\x00\x3b', 'ext': '.gif', 'min_size': 256},
    'GIF87': {'header': b'GIF87a', 'footer': b'\x00\x3b', 'ext': '.gif', 'min_size': 256},
    'BMP': {'header': b'BM', 'footer': None, 'ext': '.bmp', 'min_size': 512},
    'MP3': {'header': b'\xff\xfb', 'footer': None, 'ext': '.mp3', 'min_size': 4096},
    'MP4': {'header': b'\x00\x00\x00\x18ftyp', 'footer': None, 'ext': '.mp4', 'min_size': 4096},
    'AVI': {'header': b'RIFF', 'footer': None, 'ext': '.avi', 'min_size': 4096},
    'EXE': {'header': b'MZ\x90\x00', 'footer': None, 'ext': '.exe', 'min_size': 2048},  # Signature plus longue
    'RAR': {'header': b'Rar!\x1a\x07', 'footer': None, 'ext': '.rar', 'min_size': 1024},
    '7Z': {'header': b'7z\xbc\xaf\x27\x1c', 'footer': None, 'ext': '.7z', 'min_size': 1024},
}
