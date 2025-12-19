import struct
class PartitionAnalyzer:
    def __init__(self, logger):
        self.logger = logger
    
    def detect_mbr(self, data):
        """Détecte et analyse le MBR (Master Boot Record)"""
        if len(data) < 512:
            return None
        
        # Vérifier la signature MBR (0x55AA à la fin)
        if data[510:512] != b'\x55\xaa':
            self.logger.log("Signature MBR non trouvée", "WARN")
            return None
        
        self.logger.log("MBR détecté avec signature valide")
        partitions = []
        
        # Lire les 4 entrées de partition (offset 446)
        for i in range(4):
            offset = 446 + (i * 16)
            entry = data[offset:offset+16]
            
            if entry[0] == 0x00 and entry[4] == 0x00:  # Partition vide
                continue
            
            status = entry[0]
            partition_type = entry[4]
            lba_start = struct.unpack('<I', entry[8:12])[0]
            num_sectors = struct.unpack('<I', entry[12:16])[0]
            
            if num_sectors == 0:
                continue
            
            partition_info = {
                'number': i + 1,
                'status': 'Bootable' if status == 0x80 else 'Non-bootable',
                'type': self.get_partition_type(partition_type),
                'type_code': f"0x{partition_type:02X}",
                'start_sector': lba_start,
                'size_sectors': num_sectors,
                'size_mb': (num_sectors * 512) // (1024 * 1024)
            }
            
            partitions.append(partition_info)
            self.logger.log(f"Partition {i+1}: {partition_info['type']}, "
                          f"{partition_info['size_mb']} MB, LBA: {lba_start}")
        
        return {'type': 'MBR', 'partitions': partitions}
    
    def detect_gpt(self, data):
        """Détecte et analyse le GPT (GUID Partition Table)"""
        if len(data) < 1024:
            return None
        
        # GPT Header à LBA 1 (offset 512)
        gpt_header = data[512:1024]
        
        # Vérifier la signature GPT "EFI PART"
        if gpt_header[0:8] != b'EFI PART':
            return None
        
        self.logger.log("GPT détecté avec signature valide")
        
        num_partitions = struct.unpack('<I', gpt_header[80:84])[0]
        partition_entry_size = struct.unpack('<I', gpt_header[84:88])[0]
        
        self.logger.log(f"GPT: {num_partitions} partitions possibles")
        
        return {'type': 'GPT', 'num_partitions': num_partitions}
    
    def get_partition_type(self, type_code):
        """Convertit le code de type de partition en description"""
        types = {
            0x00: 'Vide',
            0x01: 'FAT12',
            0x04: 'FAT16 (<32MB)',
            0x05: 'Extended',
            0x06: 'FAT16',
            0x07: 'NTFS/exFAT',
            0x0B: 'FAT32',
            0x0C: 'FAT32 LBA',
            0x0E: 'FAT16 LBA',
            0x0F: 'Extended LBA',
            0x82: 'Linux Swap',
            0x83: 'Linux',
            0x85: 'Linux Extended',
            0x8E: 'Linux LVM',
            0xA5: 'FreeBSD',
            0xA6: 'OpenBSD',
            0xAF: 'macOS HFS+',
            0xEE: 'GPT Protective',
            0xEF: 'EFI System',
        }
        return types.get(type_code, f'Inconnu (0x{type_code:02X})')