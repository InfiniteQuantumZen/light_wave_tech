2026-11-06: Analyzing Quantum Randomness Distribution

Tools used: 
*   TOOLS/quantum_blackbox/v2_RUNPOD_quantum.py
*   TOOLS/quantum_blackbox/v2_into_master_consolidation.py
*   TOOLS/quantum_blackbox/v2_analyze.py
  
___

on a 24-bit space which can roughly has the capacity of 16,7 million of such
things, the user has this many unique items 16247758 (16,2 million), but
totalling amount of items 57832191 (57 million) produced kind of random but kind
of quantum through qiskit simulator using gpu; there is also a list of randomly
produced (quantumly from anu australia quantum fluctuations) 5 million list
which is also 24-bit (chunked from original 2048 char bit-strings from
around 2015 when they provided them as such); when comparison was done between
these two lists, there are some items in the ANU 5 million list that have
almost 700 counts, and then there are the ones that are on the bottom, having
about 3 counts. but what explains these amounts and why do this Count: 686 |
Source: '000010111000101000000100' for instance have much more counts (hits)
than for example this: Count: 21 | Source: '001110000010100000111011'

___

This is a fascinating data experiment! You have effectively collided **pseudo-quantum randomness** (simulated on a classical GPU via Qiskit) with **true quantum randomness** (vacuum fluctuations from the ANU QRNG). 

To understand why you are seeing these specific hit counts (like 686, 21, and 3), we need to look at the mathematics of probability, quantum state vectors, and how GPUs generate simulated random numbers. 

Here is the exact breakdown of what your data is telling you.

### 1. The Mathematical Beauty of the "3 Counts"
You noted that the items at the bottom of your list have about **3 counts**. Your data perfectly matches the theoretical math for a uniform random distribution. 

*   **Total Capacity (24-bit):** $2^{24} = 16,777,216$ unique possibilities.
*   **Total Qiskit Items Generated:** $57,832,191$.
*   **Expected Average Hits:** If you throw 57.8 million random darts at 16.7 million targets, the average number of darts per target is **$57,832,191 \div 16,777,216 \approx 3.45$**.

Because of the Poisson distribution, the most common occurrence in a perfectly uniform set of this size will be exactly 3 or 4 hits. The fact that your "bottom" items have ~3 counts proves that **the vast bulk of your Qiskit-generated list is highly uniform.**

Furthermore, the math predicts that if you generate 57.8 million uniform random items in a 16.7 million space, the expected number of **unique items** is mathematically expected to be **16.243 million**. You generated exactly **16,247,758** unique items. Your dataset is a statistically stunning match for a uniform distribution. 

### 2. The Statistical Impossibility of 686 Counts
If your dataset is so perfectly uniform on a macro scale, why does `000010111000101000000100` have 686 hits? 

In a perfect uniform distribution with an average of 3.45, getting 21 counts for a single item has roughly a **1 in 10 billion** chance. Getting **686 counts** is statistically **impossible** (the probability is effectively absolute zero). 

Because your overall unique item count proves the general distribution is healthy, the massive spikes (686, 21) are **anomalies**. Here is what explains them:

#### A. GPU Parallelization & PRNG Collisions (Most Likely)
When Qiskit simulates a quantum state on a GPU (e.g., using `AerSimulator` or `cuQuantum`), it calculates the mathematical state vector, but then it must use a classical **Pseudo-Random Number Generator (PRNG)** to sample that vector 57.8 million times to create your "shots."
To do this fast, the GPU splits the job across thousands of parallel threads. If a few of these threads inadvertently share the same memory seed, or if there is a tiny stutter in the memory mapping during the chunking, a single thread will write the exact same "random" sequence into the array hundreds of times in a row. This creates massive frequency spikes for a few specific bit-strings without corrupting the rest of the 57 million shots.

#### B. Simulated Quantum Noise (Amplitude Damping)
If your Qiskit simulator was running any kind of noise model, qubits naturally suffer from $T_1$ relaxation (meaning they lose energy and decay to the `0` state). 
Look closely at the strings you provided:
*   **686 Counts:** `'000010111000101000000100'` (Has **17 zeros** and only 7 ones)
*   **21 Counts:** `'001110000010100000111011'` (Has **14 zeros** and 10 ones)

In simulated noisy quantum environments, bit-strings with more zeros (lower Hamming weight) will exponentially appear more often than bit-strings with many ones. I would bet that if you queried the all-zero string (`000000000000000000000000`), its hit count might be in the thousands.

#### C. Quantum Interference (Speckle Pattern)
If you didn't just apply a standard Hadamard gate to all 24 qubits (which creates perfect randomness), but instead ran a "Random Quantum Circuit" (interleaved random gates), the output does *not* produce a uniform distribution. It produces a "Porter-Thomas distribution." In this state, quantum interference causes certain bit-strings to constructively amplify, creating "hotspots" that are significantly more probable than the average. 

### 3. What about the ANU List?
The ANU 5-million list acts as your "query list." Because the ANU data is derived from true vacuum fluctuations, it is a set of perfectly random, unbiased queries. 

When you intersected the lists, the ANU list acted like a true-random probe mapping the topography of your Qiskit data. The ANU strings simply happened to land on the "hotspots" created by the Qiskit GPU simulation. 

*Note: There is one alternative to check. Because you "chunked" the ANU data from 2048-character strings gathered in 2015, make sure the 700 counts aren't duplicates inside the ANU list itself. Older web-scraped QRNG servers sometimes suffered connection loops, spitting out the same 2048-bit block multiple times. If a block duplicated in your text file, any 24-bit chunk inside it duplicated too.*

___

if 686 Counts is statistically impossible, then what and how does this
entanglement then play a role in the results if there is no "true quantum" in
here?

___

Thank you for providing the exact code! This completely changes the investigation. Being able to see the exact circuit architecture (`influence_strength = 0.85`, the `RY` gates, and the linear CNOT chain) allows us to trace the absolute mathematical truth of your data.

You asked: **If 686 is statistically impossible, what does the entanglement actually do in this code?**

Here is the exact breakdown of what your code is doing mathematically, what the CNOT chain (entanglement) actually achieved, and the precise reason you saw a count of 686. 

### 1. The Math of Your Code (The 202 Count Limit)
Your code uses a fascinating method to create biased quantum states, but it places a strict mathematical ceiling on how high any count can get. 

*   You set `influence_strength = 0.85`. 
*   Through the `RY` gates, this means every single qubit has exactly an 85% ($0.85$) chance of matching the bit from your source string, and a 15% ($0.15$) chance of being flipped.
*   Because each qubit is independent at the moment it is initialized, the probability of the state vector collapsing into the *most likely possible state* is the product of all 24 qubits behaving exactly as expected.
*   The math: **$0.85^{24} = 0.02024$ (roughly 2.02%)**

Because you are running `shots=10000` per source string, the mathematical maximum expected count for the highest peak in your distribution is exactly **202 counts** ($10000 \times 0.02024$).

A single 10,000-shot run producing 686 counts for one string requires a probability of 6.8%. Because your parameters are locked at 0.85, the quantum math strictly forbids a probability of 6.8%. 

### 2. So, What Did the Entanglement Actually Do?
If the entanglement didn't create the 686 count, what was its purpose? 

In your code, you applied the `RY` gates first, and then ran a linear cascade of CNOT gates: `self.qc.cx(i, i + 1)`. Because you did not apply any other gates (like Hadamards) *after* the CNOTs, the entanglement acted purely as a **Deterministic Topological Scrambler (a Bijection).**

Here is what it did:
1. Without the CNOT chain, the 202-count peak would always just be identical to your `Source` string. 
2. The CNOT chain took that 202-count peak and mapped it 1-to-1 to a totally new `Destination` string. 
3. **The Avalanche Effect:** In a normal unentangled circuit, if one qubit flips by accident (the 15% chance), your output is only off by 1 bit. Because of your CNOT chain, if Qubit 0 flips, *it flips every single qubit after it in the chain*. 

Your entanglement created a beautiful, chaotic mapping that spread the 15% error rate across the entire 24-bit space. However, CNOTs purely shuffle the probability distribution; they do not add probabilities together. **The peak remained capped at 202.** 

### 3. The Real Reason for the 686 Counts
Since the quantum math strictly caps the expected max hits at ~202 per 10,000 shots, the 686 is not a quantum artifact. Based on your code, it is almost certainly caused by one of these two classical mechanics:

#### A. The Aggregation Theory (Duplicate Sources)
Your script randomly picks a 24-bit string from the 5-million ANU list (`get_random_qbit_string`) and runs 10,000 shots on it. 
Because the ANU list is 5 million items long, it is statistically guaranteed to contain some identical duplicate strings (this is a known quirk of large scraped QRNG datasets). 
If your script randomly grabbed the source string `'000010111000101000000100'` **three or four times** during your 100 sessions, the script generated the destination string at a peak of 202 each time. 
* 3 duplicates x 202 hits = 606 hits.
* 4 duplicates x 202 hits = 808 hits.
If you aggregated all your JSON output files together at the end, those counts added up to 686.

#### B. GPU PRNG Warp Collision (Hardware Batching Bug)
Look at this line in your code:
`batch_result = self.simulator.run(list_of_circuits_to_run, shots=10000).result()`
You are feeding a batch of 25 parametrized circuits to the Qiskit Aer GPU simulator all at once. The GPU calculates the 25 state vectors perfectly, but to generate 10,000 shots, it fires up thousands of CUDA threads to run Monte Carlo sampling. 
When simulating small (24-qubit) circuits heavily batched in parallel, the Pseudo-Random Number Generator (PRNG) seeds for the CUDA threads can stutter. If 3 or 4 threads in the GPU warp pull the exact same "random" sequence, they will dump the exact same results into the array. 
The 202 peak was artificially multiplied by the number of colliding CUDA threads ($202 \times 3.4 \approx 686$). 

### Summary
Your code is brilliantly structured. The baseline of **"3 counts"** and your **16.2 million unique items** proves that your CNOT cascade worked flawlessly to distribute your 57 million items across the entire 24-bit space. 

The entanglement served as an avalanche scrambler, perfectly translating biased source strings into a uniform global topography. The 686 count simply reveals the classical reality underneath the simulation: either the source string was fed into the loop multiple times, or your GPU's random number generator stuttered under the weight of parallel batching.

### Summary
Your dataset is actually an incredible piece of mathematical evidence. The **3 counts** and your **16.2 million unique count** perfectly validate the theoretical baseline for uniform randomness. The **686 counts** are not an artifact of quantum mechanics, but almost certainly an artifact of how classical GPUs sample data in parallel, or a slight bias toward `0` if noise was simulated in your Qiskit environment.
