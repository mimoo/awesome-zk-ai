---
title: Confidential LLM Inference across CPU and GPU TEEs
paper: tee-confidential-llm
status: reviewed
---

## What is new

The first systematic measurement of what it costs to run a *whole* LLM inference pipeline inside a
trusted execution environment, on both sides of the hardware, and end to end rather than in
fragments. Prior TEE-for-ML work offloaded only pieces of the model; this runs full Llama2 (7B,
13B, 70B) entirely inside Intel TDX and SGX, accelerated by AMX, and then runs the same workload on
an NVIDIA H100 with confidential computing enabled, so the two can be put side by side.

The paper is a benchmarking study and does not pretend otherwise. Its output is twelve numbered
"insights" and a comparison table grading each TEE on hardware, software, overhead and cost. The
useful ones for us:

- **GPU TEEs cost single-digit percentages**, and the overhead *shrinks* as batch size and input
  length grow, because the fixed costs (kernel launches, PCIe bounce-buffer transfers) amortize
  against rising arithmetic intensity.
- **CPU TEEs are not obviously worse**, and are sometimes *better*, on small models with small
  batches, an H100 sits unsaturated, and a TDX CPU can be more cost-effective *and* strictly more
  secure.
- **An entire RAG pipeline**, Elasticsearch and all, runs inside TDX at essentially the same
  overhead as bare inference.

The last one is the most under-appreciated. The confidentiality boundary can enclose the *retrieval
database*, not just the model, and that is where the sensitive documents actually live.

## What it actually proves

**That a single-GPU, 7B-class confidential deployment with unencrypted GPU memory costs a few
percent of throughput, measured against a non-confidential cloud VM.**

Every clause there is load-bearing, and the repo has been quoting the headline without them.

- **It is a confidentiality result, not a verifiability one.** The paper never mentions
  zero-knowledge proofs, zkML, or SNARKs, the strings appear **zero times**. It measures the cost
  of *hiding* the model and the prompt from the cloud operator. The TEE-versus-ZK comparison this
  repo builds on top of it is **ours**. The overhead figure transfers cleanly (it is simply the cost
  of running the model in the enclave, whatever you want the enclave for), and hardware attestation
  does buy a form of integrity. But the paper draws no comparison to proof systems and must not be
  cited as though it did.
- **The baseline is not bare metal**, and the authors say so plainly: "As our machine is rented, we
  do not have access to bare metal and present the results for raw and Confidential GPUs (cGPU)."
  The GPU comparison is confidential-Azure-VM against non-confidential-Azure-VM. For a *deployment*
  decision that is arguably the right baseline. It is not "overhead versus the hardware's ceiling."
- **The CPU latency overhead is double the throughput overhead**, and only the throughput number
  ever gets quoted. The abstract gives both.

## What to distrust

Nothing about the measurement, this is a careful, honest paper that grades its own subject harshly
and publishes the numbers that undercut it. What deserves suspicion is **how the figure is used**,
including by us. Two conditions gut the general reading.

:::audit The headline is a single-GPU number, and multi-GPU falls off a cliff
The 4–8% is the "Single resource" row of the summary table. The moment a model does not fit on one
H100, which is every model anyone would actually want to protect, you need tensor or pipeline
parallelism, and the paper reports what that costs:

> As the cGPU instances do not support RDMA and GPUdirect, all data is transferred through the CPU,
> **capping throughput at 3GB/s (considerably lower than the non-confidential 40GB/s)**.

That is better than a **13× interconnect penalty**, hitting exactly the communication pattern
multi-GPU serving depends on. The same table grades the H100 cGPU **"D (NVLINK unprotected)"** on
scale-up, the worst grade it assigns anything.

And the paper notes that a network protection scheme such as IPsec "is required on top of both CPUs
and GPUs, which also introduces an overhead of up to 90%." That is not in the 4–8% either.
:::

:::audit And the 4–8% buys a TEE that does not encrypt GPU memory
> **H100s do not encrypt their HBM memory [31], compared to CPUs that do.**

The summary table grades the H100 cGPU **"B (HBM unencrypted)"** on memory, *weaker than the Intel
CPU TEEs it is being benchmarked against*, which score C. So the cheap TEE is also the leakier one,
and the comparison flatters it twice.

The authors then say what closing the gap will cost:

> While B100s address these issues, **we expect that they will add a non-negligible overhead to
> H100s' results, since we identified memory encryption as a significant cost in CPUs.**

The people who produced the number expect the number to get worse as the hardware gets more secure.
:::

**Does the strategic claim survive?** Yes, and this is worth stating clearly, because the honest
reading is still bad news for zkML. Even if you triple the overhead to absorb the memory encryption
the H100 is currently skipping, and even if you take the multi-GPU penalty seriously, TEE-protected
inference remains **three orders of magnitude** cheaper than proving the same forward pass. The
argument in [alternatives](../../alternatives/) does not depend on the difference between 4% and
40%; it depends on the difference between *tens of percent* and *a thousand times*, and that gap is
not in doubt.

What changes is the *rhetoric*. "TEEs cost 4–8%" is not a constant of nature, it is the best corner
of a cost surface, measured on the smallest interesting model, on one GPU, with a security hole
open. The defensible sentence is the conditional one, and the SoK should use it.

**The one thing the paper cannot tell you** is the thing the whole argument actually turns on:
whether the verifier is willing to trust NVIDIA's attestation chain. That is not a performance
question, and no benchmark will settle it. ZK's entire claim to relevance is that some verifiers, 
an adversarial counterparty, a regulator, a public chain, structurally cannot make that assumption.
This paper prices the alternative; it does not price the trust.
