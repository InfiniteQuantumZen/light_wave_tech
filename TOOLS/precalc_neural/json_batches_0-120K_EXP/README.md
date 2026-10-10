experimentation in extending value range to 120K for new dataset used for training new neural net with v3_OPTIMIZED_trainer.py using ContinuousIntegerDataset, embed_size=256, num_heads=8, num_layers=8

2026-10-10: 
**  2754 json INT files >> BITWISE >> OUTPUT_1 eigen_bitmask = (audio_eigenvalues * 65535).astype(np.int32)
**  2754 json INT files >> PROBABILITY_SWAP >> OUTPUT_2 eigen_bitmask = (audio_eigenvalues * 65535).astype(np.int32)
  **  THESE OUTPUT_1 + OUTPUT_2 (5504 json INT files) >> BITWISE >> eigen_bitmask = (audio_eigenvalues * 92535).astype(np.int32)
**  AND THESE THROUGH shuffle_final_output.py
