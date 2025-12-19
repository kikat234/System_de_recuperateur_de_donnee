from datetime import datetime
class ReportGenerator:
    def __init__(self, logger):
        self.logger = logger
    
    def generate_report(self, report_data, output_file):
        """Génère un rapport détaillé au format texte"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("RAPPORT DE RÉCUPÉRATION DE DONNÉES\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Date du rapport: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Source analysée: {report_data.get('source', 'N/A')}\n")
                f.write(f"Taille totale: {report_data.get('total_size', 0):,} octets\n\n")
                
                # Section Récupérabilité
                f.write("-" * 80 + "\n")
                f.write("1. ANALYSE DE RÉCUPÉRABILITÉ\n")
                f.write("-" * 80 + "\n")
                score = report_data.get('recoverability_score', 0)
                f.write(f"Score de récupérabilité: {score:.2f}%\n")
                if score > 70:
                    f.write("Évaluation: EXCELLENTE - Les données sont en bon état\n")
                elif score > 40:
                    f.write("Évaluation: MOYENNE - Récupération partielle possible\n")
                else:
                    f.write("Évaluation: FAIBLE - Données fortement corrompues\n")
                f.write("\n")
                
                # Section Partitions
                if 'partitions' in report_data:
                    f.write("-" * 80 + "\n")
                    f.write("2. PARTITIONS DÉTECTÉES\n")
                    f.write("-" * 80 + "\n")
                    partitions = report_data['partitions']
                    if partitions and 'partitions' in partitions:
                        for part in partitions['partitions']:
                            f.write(f"\nPartition {part['number']}:\n")
                            f.write(f"  Type: {part['type']}\n")
                            f.write(f"  Statut: {part['status']}\n")
                            f.write(f"  Taille: {part['size_mb']:,} MB\n")
                            f.write(f"  Secteur de début: {part['start_sector']}\n")
                    else:
                        f.write("Aucune partition détectée\n")
                    f.write("\n")
                
                # Section Systèmes de fichiers
                if 'filesystems' in report_data:
                    f.write("-" * 80 + "\n")
                    f.write("3. SYSTÈMES DE FICHIERS\n")
                    f.write("-" * 80 + "\n")
                    for fs in report_data['filesystems']:
                        f.write(f"\nType: {fs['type']}\n")
                        f.write(f"Taille: {fs.get('volume_size_mb', 'N/A')} MB\n")
                        if 'oem_name' in fs:
                            f.write(f"OEM: {fs['oem_name']}\n")
                    f.write("\n")
                
                # Section Fichiers récupérés
                f.write("-" * 80 + "\n")
                f.write("4. FICHIERS DÉTECTÉS (SIGNATURE SCAN)\n")
                f.write("-" * 80 + "\n")
                files = report_data.get('recovered_files', [])
                f.write(f"Total de fichiers détectés: {len(files)}\n\n")
                
                # Statistiques par type
                file_types = {}
                for file_info in files:
                    ftype = file_info['type']
                    file_types[ftype] = file_types.get(ftype, 0) + 1
                
                f.write("Répartition par type:\n")
                for ftype, count in sorted(file_types.items()):
                    f.write(f"  {ftype}: {count} fichier(s)\n")
                f.write("\n")
                
                # Liste détaillée
                f.write("Liste détaillée:\n")
                for idx, file_info in enumerate(files, 1):
                    f.write(f"\n  [{idx:04d}] {file_info['type']}\n")
                    f.write(f"        Offset: 0x{file_info['offset']:08X}\n")
                    if 'size' in file_info:
                        f.write(f"        Taille: {file_info['size']:,} octets\n")
                    if 'extracted' in file_info and file_info['extracted']:
                        f.write(f"        Fichier: {file_info.get('filename', 'N/A')}\n")
                
                f.write("\n")
                f.write("-" * 80 + "\n")
                f.write("FIN DU RAPPORT\n")
                f.write("=" * 80 + "\n")
            
            self.logger.log(f"Rapport généré: {output_file}")
            return True
        except Exception as e:
            self.logger.log(f"Erreur génération rapport: {e}", "ERROR")
            return False
