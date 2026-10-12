Here you can find NeuralTrainer that is one part of the inner workings of Light Wave Tech. 

How the dataset and the signal came to be and evolves: 
*  [1. Some variation/version of this montecarlo.py] (https://github.com/InfiniteQuantumZen/light_wave_tech/blob/main/NeuralTrainer/early_prototype_qbit_montecarlo_random_walk/montecarlo.py)
*  [2. Some amount of this quantum.php](https://github.com/InfiniteQuantumZen/light_wave_tech/blob/main/NeuralTrainer/early_prototype_qbit_montecarlo_random_walk/quantum.php)
*  [3. Neural Network and its outputs](https://github.com/InfiniteQuantumZen/light_wave_tech/tree/main/NeuralTrainer) tiny model with settings batch_size=256, seq_length=128, embed_size=256, num_heads=4, num_layers=4
*  [4. SUNO ELARA Signal + Eigen Nudge](https://github.com/InfiniteQuantumZen/light_wave_tech/tree/main/TOOLS/precalc_neural/json_batches_0-120K_EXP)
*  [5. Bigger Neural Network](https://github.com/InfiniteQuantumZen/light_wave_tech/blob/main/NeuralTrainer/LOCAL_v5_OPTIMIZED_trainer.py) with settings batch_size=512, patch_size=16, seq_length=1024, embed_size=512, num_heads=8, num_layers=8

In the /early_prototype_qbit_montecarlo_random_walk you can find files that are 
a selection of legacy prototypes that were experimentations of QBITS from Quantum fluctuations 
(the user had over 5 million stored from their experimentations from 2014-2017) from Quantum computing - 
Physics @ ANU public interface, used in their php + mysql things... 

alongside with some montecarlo random walks, which combined led 
to the dataset used in current NeuralTrainer as base. 
Included are also some c (cuda) prototypes of random-walking eurojackpot universe 
(there is visible pattern inherent if one but see...) and php front-end that were 
also basis for the birth of Light Wave Tech with their ideas of 
deep structures (holofractographic) and emergence of intelligence.
