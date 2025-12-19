class DataAnalyzer:
    def __init__(self, logger):
        self.logger = logger
    
    def estimate_recoverability(self, data, block_size=4096):
        """Estime le taux de récupérabilité basé sur l'intégrité des blocs"""
        if not data:
            return 0.0
        
        total_blocks = len(data) // block_size
        if total_blocks == 0:
            return 0.0
        
        valid_blocks = 0
        zero_blocks = 0
        
        for i in range(total_blocks):
            block = data[i*block_size:(i+1)*block_size]
            # Un bloc est considéré valide s'il contient des données variées
            unique_bytes = len(set(block))
            
            if all(b == 0 for b in block):
                zero_blocks += 1
            elif unique_bytes > 10:  # Bloc avec diversité de données
                valid_blocks += 1
        
        # Score basé sur les blocs valides
        score = (valid_blocks / total_blocks) * 100
        
        self.logger.log(f"Analyse: {valid_blocks} blocs valides, {zero_blocks} blocs vides sur {total_blocks} - Score: {score:.2f}%")
        return score
