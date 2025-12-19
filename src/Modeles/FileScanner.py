from Modeles.SignatureFichiers import FILE_SIGNATURES
import struct
# Import optionnel de PIL pour l'aperçu d'images
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  Pillow n'est pas installé. Les aperçus d'images ne seront pas disponibles.")
    print("   Pour installer : pip install Pillow")
class FileScanner:
    def __init__(self, logger):
        self.logger = logger
        self.signatures = FILE_SIGNATURES
        
    def _is_file_like(self, data):
        return hasattr(data, 'read') and hasattr(data, 'seek')

    def _read_range(self, data, start, length):
        """Lit une plage depuis `data` qu'il soit bytes/mmap ou file-like."""
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
    
    def scan_signatures(self, data, progress_callback=None, enable_filtering=True, selected_types=None):
        """Scanne les données pour trouver des signatures de fichiers"""
        # ← Filtrer les signatures selon les types sélectionnés
        signatures_to_scan = self.signatures
        
        if selected_types:
            signatures_to_scan = {k: v for k, v in self.signatures.items() if k in selected_types}
        
        # Taille totale
        try:
            if self._is_file_like(data):
                cur = data.tell()
                data.seek(0, 2)
                total_len = data.tell()
                data.seek(cur if cur is not None else 0)
            else:
                total_len = len(data)
        except Exception:
            total_len = 0

        self.logger.log(f"Début du scan de signatures sur {total_len:,} octets - Types: {list(signatures_to_scan.keys())}")
        found_files = []

        chunk_size = 1024 * 1024  # 1 MB

        # Pour gérer signatures traversant les frontières
        max_header_len = max((len(sig['header']) for sig in signatures_to_scan.values()), default=1)
        overlap = max_header_len - 1

        if self._is_file_like(data):
            base = 0
            prev_tail = b''
            data.seek(0)
            while base < total_len:
                read = data.read(chunk_size)
                if not read:
                    break
                chunk = prev_tail + read

                for file_type, sig in signatures_to_scan.items():
                    header = sig['header']
                    pos = 0
                    while True:
                        pos = chunk.find(header, pos)
                        if pos == -1:
                            break
                        actual_offset = base - len(prev_tail) + pos
                        if actual_offset < 0:
                            pos += 1
                            continue
                        if actual_offset >= total_len:
                            break
                        if not any(f['offset'] == actual_offset for f in found_files):
                            if self.validate_signature(data, actual_offset, file_type, sig):
                                found_files.append({'type': file_type, 'offset': actual_offset, 'signature': sig})
                                self.logger.log(f"Trouvé {file_type} à l'offset 0x{actual_offset:08X}")
                        pos += 1

                # progression
                base += len(read)
                if progress_callback and total_len:
                    progress = (base / total_len) * 100
                    progress_callback(min(progress, 100))

                # garder l'overlap
                prev_tail = chunk[-overlap:] if overlap > 0 else b''

        else:
            # data est bytes-like
            for chunk_idx in range(0, total_len, chunk_size):
                chunk = data[chunk_idx:chunk_idx+chunk_size]

                for file_type, sig in signatures_to_scan.items():
                    header = sig['header']
                    pos = 0
                    while True:
                        pos = chunk.find(header, pos)
                        if pos == -1:
                            break
                        actual_offset = chunk_idx + pos
                        if not any(f['offset'] == actual_offset for f in found_files):
                            if self.validate_signature(data, actual_offset, file_type, sig):
                                found_files.append({'type': file_type, 'offset': actual_offset, 'signature': sig})
                                self.logger.log(f"Trouvé {file_type} à l'offset 0x{actual_offset:08X}")
                        pos += 1

                if progress_callback and total_len:
                    progress = ((chunk_idx + chunk_size) / total_len) * 100
                    progress_callback(min(progress, 100))
        
        # Filtrage des faux positifs
        if enable_filtering:
            found_files = self.filter_false_positives(data, found_files)
        
        self.logger.log(f"Scan terminé: {len(found_files)} fichiers détectés")
        return found_files
    
    def validate_signature(self, data, offset, file_type, sig):
        """Validation supplémentaire de la signature"""
        # obtenir taille totale
        try:
            if self._is_file_like(data):
                cur = data.tell()
                data.seek(0, 2)
                total_len = data.tell()
                data.seek(cur if cur is not None else 0)
            else:
                total_len = len(data)
        except Exception:
            total_len = 0

        if offset + len(sig['header']) > total_len:
            return False

        # Validation spécifique par type
        if file_type == 'DOCX' or file_type == 'XLSX':
            # Pour DOCX/XLSX, vérifier la présence de chaînes caractéristiques
            preview = self._read_range(data, offset, 200)
            if file_type == 'DOCX':
                # DOCX contient "word/" dans son structure ZIP
                if b'word/' not in self._read_range(data, offset, 2000):
                    return False
            elif file_type == 'XLSX':
                # XLSX contient "xl/" dans son structure ZIP
                if b'xl/' not in self._read_range(data, offset, 2000):
                    return False

        elif file_type == 'PDF':
            # PDF doit avoir %PDF suivi d'un numéro de version
            preview = self._read_range(data, offset, 20)
            if not (b'%PDF-1.' in preview or b'%PDF-2.' in preview):
                return False

        elif file_type == 'EXE':
            # Vérifier PE header pour les EXE Windows
            if offset + 64 < total_len:
                # L'offset du PE header est à 0x3C
                pe_offset_pos = offset + 0x3C
                if pe_offset_pos + 4 <= total_len:
                    pe_offset = struct.unpack('<I', self._read_range(data, pe_offset_pos, 4))[0]
                    if offset + pe_offset + 4 <= total_len:
                        pe_sig = self._read_range(data, offset + pe_offset, 2)
                        if pe_sig != b'PE':
                            return False
                    else:
                        return False

        elif file_type == 'MP3':
            # MP3 : vérifier le frame header
            if offset + 4 <= total_len:
                # Frame sync doit être 11 bits à 1
                header_bytes = self._read_range(data, offset, 4)
                if len(header_bytes) >= 2:
                    if (header_bytes[0] == 0xFF and (header_bytes[1] & 0xE0) == 0xE0):
                        return True
                    return False

        return True
    
    def filter_false_positives(self, data, found_files):
        """Filtre les faux positifs détectés"""
        filtered = []
        self.logger.log(f"Filtrage des faux positifs sur {len(found_files)} fichiers...")
        
        for file_info in found_files:
            offset = file_info['offset']
            file_type = file_info['type']
            sig = file_info['signature']
            
            # Vérifier la taille minimale
            min_size = sig.get('min_size', 100)
            
            # Estimer la taille du fichier
            end_offset = self.estimate_file_end_quick(data, offset, file_type, sig)
            estimated_size = end_offset - offset
            
            # Filtrer si trop petit
            if estimated_size < min_size:
                self.logger.log(f"Filtré {file_type} à 0x{offset:08X} (taille: {estimated_size} < {min_size})", "WARN")
                continue
            
            # Filtrer les offsets suspects (trop proches)
            is_duplicate = False
            for existing in filtered:
                if existing['type'] == file_type and abs(existing['offset'] - offset) < 64:
                    is_duplicate = True
                    break
            
            if is_duplicate:
                self.logger.log(f"Filtré {file_type} à 0x{offset:08X} (doublon proche)", "WARN")
                continue
            
            filtered.append(file_info)
        
        self.logger.log(f"Après filtrage: {len(filtered)} fichiers conservés")
        return filtered
    
    def estimate_file_end_quick(self, data, start, file_type, sig):
        """Estimation rapide de la fin du fichier"""
        max_size = 10 * 1024 * 1024  # 10 MB max
        
        if sig['footer']:
            # Chercher le footer
            search_end = min(start + max_size, len(data))
            search_data = data[start:search_end]
            footer_pos = search_data.find(sig['footer'])
            if footer_pos != -1:
                return start + footer_pos + len(sig['footer'])
        
        # Sinon estimation par défaut
        return min(start + 5000, len(data))  # 5KB par défaut pour estimation rapide
