import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

class PitchVisualizer:
    def __init__(self, style="whitegrid"):
        sns.set_theme(style=style)

    def plot_movement(self, df: pd.DataFrame, pitcher_name: str):
        """
        Plots Horizontal Break vs Induced Vertical Break (IVB).
        The 'signature' plot for any MLB pitcher.
        """
        plt.figure(figsize=(10, 8))
        
        # Convert horizontal movement to inches for consistent units
        df = df.copy()
        df['hb_in'] = df['pfx_x'] * 12
        
        sns.scatterplot(
            data=df, 
            x='hb_in', 
            y='ivb', 
            hue='pitch_type', 
            style='pitch_type',
            s=100,
            alpha=0.7,
            palette='Set1'
        )
        
        # Add crosshairs for the origin
        plt.axhline(0, color='black', linewidth=1, alpha=0.5)
        plt.axvline(0, color='black', linewidth=1, alpha=0.5)
        
        plt.title(f"Pitch Movement Profile: {pitcher_name}", fontsize=16, fontweight='bold')
        plt.xlabel("Horizontal Break (inches)", fontsize=12)
        plt.ylabel("Induced Vertical Break (inches)", fontsize=12)
        plt.legend(title="Pitch Type", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, linestyle='--', alpha=0.6)
        
        plt.tight_layout()
        plt.show()