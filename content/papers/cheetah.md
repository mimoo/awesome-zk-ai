---
title: Cheetah
paper: cheetah
status: reviewed
---

Promoted from an `external:` stub in the citation graph to a real paper, and the promotion is the
point.

Cheetah is one of the **three nodes this SoK's headline finding rests on**, *the only three papers
cited by both columns are [[sirnn]], Cheetah and [[secfloat]], and all three are MPC numerics.* We
held SecFloat's PDF. Cheetah was a name in a graph. We had been arguing from it without reading it.

## What is new

**A rotation-free homomorphic linear layer.** By coefficient-encoding the convolution instead of using
SIMD/CRT packing, a whole CONV or FC layer becomes a **single homomorphic polynomial multiplication**, 
no HE rotations at all. That lets Cheetah drop the lattice dimension from 8192 to 4096 and accept
secret shares from $\mathbb{Z}_{2^\ell}$ for free.

[[iron]], [[bolt]], BumbleBee and [[nimbus]] all inherit this encoding. When you read a 2024
private-transformer paper and find a coefficient-encoded matmul, you are reading Cheetah.

Its other half is VOLE-style **silent OT** (Ferret) for comparison and truncation, 11.6× less
communication than CrypTFlow2 on the millionaires' protocol, 12× on truncation, and **88× when the
MSB is known**.

## And its truncation is approximate, on purpose

This is why the paper matters to [the numerics page](/numerics/), and it is not what it is famous for.

Cheetah **deliberately keeps a 1-bit truncation error** (probability $1/2$) and eliminates only the
"harsh" error. The saving is enormous: $13\ell$ bits of communication against CrypTFlow2's faithful
$\lambda(\ell + f + 2) + 19\ell + 14f$.

That is the MPC bargain, made explicitly: **accept a bounded, benign error and pay far less.**

And it is exactly the trade [ZK cannot take](/numerics/). In MPC the error is benign because the input
is not adversarial. In ZK the prover *chooses* the input, so a bounded error with probability $1/2$ is
not an accuracy cost, it is a soundness hole the prover steers into. Cheetah is the cleanest primary
source for that contrast, and it sits right next to [[sirnn]], whose truncation is *exact* and *also*
cheap.

Two papers, same authors' community, same year, one probabilistic and one exact, and the ZK world
borrowed the exact one without ever citing either.

## The crossing edge

Adding Cheetah as a real paper creates the first citation edge in this corpus that crosses from the
verifiability column into the privacy column: **[[hao-et-al]] → Cheetah.**

Before you believe it means anything: it is a **bibliography-only** citation. Cheetah is reference
[30] in [[hao-et-al]] and appears **zero times in its body**. Contrast [[sirnn]], reference [47],
which appears **five times in the body** and is load-bearing.

The full argument is on [the bridge page](/numerics/bridge/). The short version: the two columns still
do not read each other as cryptography.

## What to distrust

Little, and the paper is careful. The one thing to note is that **no accuracy delta is reported**. The
evidence is that on ~1000 ImageNet images Cheetah "outputs the same classification label as SCI_HE", 
which is a statement about agreement with another *secure* system, not about agreement with the float
model. And its own DELPHI comparison is caveated: Cheetah matches [[delphi]] "if we assume the harsh
truncation error in DELPHI does not occur on shallow NNs."
