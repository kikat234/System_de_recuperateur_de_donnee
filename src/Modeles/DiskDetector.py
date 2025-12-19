import platform
import subprocess
class DiskDetector:
    @staticmethod
    def list_disks():
        """Liste les disques disponibles selon l'OS"""
        system = platform.system()
        disks = []
        
        if system == "Windows":
            import string
            try:
                from ctypes import windll
                drives = []
                bitmask = windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drive = f"{letter}:\\"
                        try:
                            drive_type = windll.kernel32.GetDriveTypeW(drive)
                            if drive_type == 2:  # DRIVE_REMOVABLE
                                drives.append((drive, "USB/Amovible"))
                            elif drive_type == 3:  # DRIVE_FIXED
                                drives.append((drive, "Disque fixe"))
                        except:
                            pass
                    bitmask >>= 1
                return drives
            except:
                return []
            
        elif system == "Linux":
            try:
                result = subprocess.run(['lsblk', '-ndo', 'NAME,TYPE,SIZE'], 
                                      capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'disk' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            disks.append((f"/dev/{parts[0]}", f"{parts[2]}"))
            except:
                pass
            return disks
            
        elif system == "Darwin":  # macOS
            try:
                result = subprocess.run(['diskutil', 'list'], 
                                      capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if '/dev/disk' in line:
                        parts = line.split()
                        if parts:
                            disks.append((parts[0], "Disque"))
            except:
                pass
            return disks
        
        return disks
