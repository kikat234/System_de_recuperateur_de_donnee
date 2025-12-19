import os
from Modeles.SignatureFichiers import FILE_SIGNATURES
class FileCarver:
    def __init__(self, logger):
        self.logger = logger
    
    def _is_file_like(self, data):
        return hasattr(data, 'read') and hasattr(data, 'seek')

    def _read_range(self, data, start, length):
        if self._is_file_like(data):
            try:
                cur = data.tell()
            except Exception:
                cur = None
            data.seek(start)
            res = data.read(length)
            if cur is not None:
                try:
                    data.seek(cur)
                except Exception:
                    pass
            return res
        else:
            return data[start:start+length]
    
    def carve_file(self, data, file_info, max_size=50*1024*1024):
        """Extrait un fichier à partir d'un offset donné"""
        offset = file_info['offset']
        sig = file_info['signature']
        file_type = file_info['type']
        
        self.logger.log(f"Carving {file_type} à l'offset 0x{offset:08X}")
        
        # Trouver la fin du fichier
        if sig['footer']:
            # Chercher le footer dans une zone raisonnable
            if self._is_file_like(data):
                # lecture en streaming
                search_end = offset + max_size
                cur = data.tell()
                data.seek(offset)
                buf = data.read(max_size)
                data.seek(cur)
                footer_pos = buf.find(sig['footer'])
                if footer_pos != -1:
                    end_offset = offset + footer_pos + len(sig['footer'])
                else:
                    end_offset = self.estimate_file_end(data, offset, file_type, max_size)
            else:
                search_end = min(offset + max_size, len(data))
                search_data = data[offset:search_end]
                footer_pos = search_data.find(sig['footer'])
                if footer_pos != -1:
                    end_offset = offset + footer_pos + len(sig['footer'])
                else:
                    end_offset = self.estimate_file_end(data, offset, file_type, max_size)
        else:
            end_offset = self.estimate_file_end(data, offset, file_type, max_size)

        if self._is_file_like(data):
            # seek to offset and read
            try:
                cur = data.tell()
            except Exception:
                cur = None
            data.seek(offset)
            file_data = data.read(end_offset - offset)
            if cur is not None:
                try:
                    data.seek(cur)
                except Exception:
                    pass
        else:
            file_data = data[offset:end_offset]
        
        if len(file_data) < 100:  # Fichier trop petit
            self.logger.log(f"Fichier {file_type} trop petit ({len(file_data)} octets), ignoré", "WARN")
            return None
        
        return file_data
    
    def estimate_file_end(self, data, start_offset, file_type, max_size):
        """Estime la fin d'un fichier sans footer"""
        # Stratégies selon le type
        if file_type in ['JPEG']:
            # JPEG: chercher le marqueur de fin 0xFFD9
            if self._is_file_like(data):
                cur = data.tell()
                data.seek(start_offset)
                buf = data.read(max_size)
                data.seek(cur)
                pos = buf.find(b'\xff\xd9')
                if pos != -1:
                    return start_offset + pos + 2
            else:
                search_end = min(start_offset + max_size, len(data))
                for i in range(start_offset, search_end - 1):
                    if data[i:i+2] == b'\xff\xd9':
                        return i + 2
        
        elif file_type in ['PNG']:
            # PNG: chercher IEND
            if self._is_file_like(data):
                cur = data.tell()
                data.seek(start_offset)
                buf = data.read(max_size)
                data.seek(cur)
                iend_pos = buf.find(b'IEND')
                if iend_pos != -1:
                    return start_offset + iend_pos + 8
            else:
                search_end = min(start_offset + max_size, len(data))
                search_data = data[start_offset:search_end]
                iend_pos = search_data.find(b'IEND')
                if iend_pos != -1:
                    return start_offset + iend_pos + 8
        
        elif file_type in ['PDF']:
            # PDF: chercher %%EOF
            if self._is_file_like(data):
                cur = data.tell()
                data.seek(start_offset)
                buf = data.read(max_size)
                data.seek(cur)
                eof_pos = buf.find(b'%%EOF')
                if eof_pos != -1:
                    return start_offset + eof_pos + 5
            else:
                search_end = min(start_offset + max_size, len(data))
                search_data = data[start_offset:search_end]
                eof_pos = search_data.find(b'%%EOF')
                if eof_pos != -1:
                    return start_offset + eof_pos + 5
        
        # Par défaut, détecter une longue séquence de zéros ou fin de données
        block_size = 4096
        end_offset = start_offset + block_size

        if self._is_file_like(data):
            cur = data.tell()
            while end_offset < start_offset + max_size:
                data.seek(end_offset)
                block = data.read(block_size)
                if not block:
                    break
                if block.count(b'\x00') > block_size * 0.8:
                    try:
                        data.seek(cur)
                    except Exception:
                        pass
                    return end_offset
                end_offset += block_size
            try:
                data.seek(cur)
            except Exception:
                pass
            return min(start_offset + max_size, end_offset)
        else:
            while end_offset < min(start_offset + max_size, len(data)):
                block = data[end_offset:end_offset+block_size]
                if block.count(b'\x00') > block_size * 0.8:
                    return end_offset
                end_offset += block_size
            return min(start_offset + max_size, len(data))
    
    def save_carved_file(self, file_data, file_type, output_dir, index):
        """Sauvegarde un fichier extrait"""
        os.makedirs(output_dir, exist_ok=True)
        
        ext = FILE_SIGNATURES[file_type]['ext']
        filename = f"recovered_{file_type}_{index:04d}{ext}"
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'wb') as f:
                f.write(file_data)
            self.logger.log(f"Fichier sauvegardé: {filepath} ({len(file_data):,} octets)")
            return filepath
        except Exception as e:
            self.logger.log(f"Erreur lors de la sauvegarde: {e}", "ERROR")
            return None
