import struct
class FileSystemAnalyzer:
    def __init__(self, logger):
        self.logger = logger
    
    def detect_filesystem(self, data):
        """Détecte le type de système de fichiers"""
        fs_info = []
        
        # FAT16/FAT32
        fat_info = self.detect_fat(data)
        if fat_info:
            fs_info.append(fat_info)
        
        # NTFS
        ntfs_info = self.detect_ntfs(data)
        if ntfs_info:
            fs_info.append(ntfs_info)
        
        # EXT2/3/4
        ext_info = self.detect_ext(data)
        if ext_info:
            fs_info.append(ext_info)
        
        return fs_info
    
    def detect_fat(self, data):
        """Détecte FAT16/FAT32"""
        if len(data) < 512:
            return None
        
        # Vérifier le boot sector FAT
        jump_code = data[0:3]
        if jump_code[0] not in [0xEB, 0xE9]:
            return None
        
        # OEM Name
        oem_name = data[3:11].decode('ascii', errors='ignore').strip()
        
        # Bytes per sector
        bytes_per_sector = struct.unpack('<H', data[11:13])[0]
        if bytes_per_sector not in [512, 1024, 2048, 4096]:
            return None
        
        sectors_per_cluster = data[13]
        reserved_sectors = struct.unpack('<H', data[14:16])[0]
        num_fats = data[16]
        root_entries = struct.unpack('<H', data[17:19])[0]
        
        # Déterminer FAT12/16/32
        total_sectors_16 = struct.unpack('<H', data[19:21])[0]
        total_sectors_32 = struct.unpack('<I', data[32:36])[0]
        total_sectors = total_sectors_32 if total_sectors_16 == 0 else total_sectors_16
        
        fat_type = "FAT32" if root_entries == 0 else "FAT16"
        
        volume_size_mb = (total_sectors * bytes_per_sector) // (1024 * 1024)
        
        self.logger.log(f"Système de fichiers {fat_type} détecté: {volume_size_mb} MB")
        
        return {
            'type': fat_type,
            'oem_name': oem_name,
            'bytes_per_sector': bytes_per_sector,
            'sectors_per_cluster': sectors_per_cluster,
            'total_sectors': total_sectors,
            'volume_size_mb': volume_size_mb
        }
    
    def detect_ntfs(self, data):
        """Détecte NTFS"""
        if len(data) < 512:
            return None
        
        # Vérifier le boot sector NTFS
        if data[3:11] != b'NTFS    ':
            return None
        
        bytes_per_sector = struct.unpack('<H', data[11:13])[0]
        sectors_per_cluster = data[13]
        total_sectors = struct.unpack('<Q', data[40:48])[0]
        
        volume_size_mb = (total_sectors * bytes_per_sector) // (1024 * 1024)
        
        self.logger.log(f"Système de fichiers NTFS détecté: {volume_size_mb} MB")
        
        return {
            'type': 'NTFS',
            'bytes_per_sector': bytes_per_sector,
            'sectors_per_cluster': sectors_per_cluster,
            'total_sectors': total_sectors,
            'volume_size_mb': volume_size_mb
        }
    
    def detect_ext(self, data):
        """Détecte EXT2/3/4"""
        if len(data) < 2048:
            return None
        
        # Le superblock EXT est à l'offset 1024
        superblock = data[1024:1024+1024]
        
        # Magic number EXT (0xEF53)
        magic = struct.unpack('<H', superblock[56:58])[0]
        if magic != 0xEF53:
            return None
        
        total_inodes = struct.unpack('<I', superblock[0:4])[0]
        total_blocks = struct.unpack('<I', superblock[4:8])[0]
        block_size = 1024 << struct.unpack('<I', superblock[24:28])[0]
        
        volume_size_mb = (total_blocks * block_size) // (1024 * 1024)
        
        fs_type = "EXT2/3/4"
        
        self.logger.log(f"Système de fichiers {fs_type} détecté: {volume_size_mb} MB")
        
        return {
            'type': fs_type,
            'total_inodes': total_inodes,
            'total_blocks': total_blocks,
            'block_size': block_size,
            'volume_size_mb': volume_size_mb
        }
