---
title: Zator
paper: zator
status: draft
---

## What is new

Everything else in this section fits the whole computation trace into one circuit and then
fights the size of it. Zator asks the other question: **fold the network one layer at a time.**
It is the first system in this file to prove a neural network with an *incrementally verifiable
computation* scheme rather than a monolithic one — Nova folds a per-layer R1CS step circuit N
times into a single relaxed instance, and only that one instance is handed to Spartan and
actually proven. Two years before [[zktorch]] made accumulation respectable with a paper, a
week-long hackathon project made the argument with a running system.

It is worth being precise about what "first" means here, because Zator is not a paper, was not
reviewed, and does not claim to be a research contribution. It is an existence proof, and the
thing it proves the existence of is the design pattern the accumulation line is built on.

## What it actually proves

**One forward pass of a 512-layer convolutional network on one MNIST digit, quantized, against
weights the proof commits to — in three proofs, not one.**

The commitment structure is the part worth studying, and it is genuinely nice. Each backbone
step takes the previous layer's activation hash as a public input, re-hashes the activations it
was handed, and checks the two agree — so the chain of steps cannot be spliced. Alongside it
runs a *running hash* of the weights, $p_n = H(p_{n-1} \| H(W_n) \| H(b_n))$, which means the
final folded instance is bound to one specific model and not merely to *some* model of the right
shape. That is the model-substitution defence, built directly into the step circuit, and it is
the reason the weight *hashing* — not the weight arithmetic — ends up driving the design.

The three proofs are the tell. Nova can only fold a step function that is the same every time,
and a network's first and last layers are not the same as its middle: the head has to project
the image into the working space, the tail has to produce output probabilities. So the system
emits one proof for the head, one folded proof for the 510-layer backbone, and one for the tail,
and the verifier has to check all three *and* trace the public outputs across them to confirm
they came from the same execution. The README is candid that this is a workaround, and names
SuperNova as the fix, with a footnote that SuperNova was not implemented yet.

## What the benchmark shows, which is not what the headline says

The headline is depth — a network "as deep or deeper than the majority of production AI models
today", roughly two and a half billion constraints. The table above it is MNIST, and the better
part of a working day of proving.

**Read the two together and the lesson is that depth was never the binding constraint.** Nova
does dissolve it, exactly as advertised: the recursive overhead really is about ten thousand
constraints per step, negligible against the layer being proven. And the field still could not
prove a useful model afterwards — because the cost was never in the *number* of layers, it was
in the *width* of each one, and folding does nothing whatsoever about width. Zator is the clean
experiment that shows this, and it shows it by winning: it went deeper than anything else in
this file, and arrived at a handwritten-digit classifier.

The sweep across layers-per-step makes the same point from the other side. Cutting the number of
folds by folding three layers at a time makes proving *slower*, not faster, and it makes
verification substantially worse, because the final Spartan proof is now over a step circuit
three times the size. There is no win hiding on the folding axis. The fold was never the
expensive part.

:::audit  The homogeneity tax is a real cost and nobody else prices it
Zator's backbone is 510 *identical* convolution layers, and the network was designed that way
because the prover demanded it. Convolutions rather than dense layers for the same reason: the
step circuit must *hash* its weights to bind them to the running commitment, and the README
prices a single 784×784 dense layer at "~350M constraints to hash when using 220 rotations on
MiMC" — before proving one multiplication.

So the deepest network anyone had snarked is a stack of clones with no dense layer in it, and
this is not an incidental choice. It is what folding costs when the step function has to be
uniform. Every later folding system inherits this bill and pays it somewhere: [[zktorch]] pays
it in a compiler that decomposes a heterogeneous model graph into basic blocks, and in the
seven of those blocks that have no accumulation support and must be steered around.
:::

## What to distrust

**No accuracy number exists.** Not a delta, not an absolute. The model is quantized with scale
factors and floor division, the bit width is never stated, and the README volunteers that the
resulting error is "a significant limitation of the network we snarked". A proof that a
quantized network computed what it computed is worth exactly as much as the network, and we have
no evidence about the network. This is not a hidden flaw — it is disclosed, and the project
explicitly defers performance and compilation quality to [[ezkl]] — but it does mean no
correctness claim here transfers to anything.

**The benchmark is the backbone, not the system.** The table measures 510 folded layers. Head
and tail are proven separately and their costs are never reported, so there is no end-to-end
number for the 512-layer network the title advertises. The gap is small in relative terms and
large in principle: the advertised artifact and the measured artifact are not the same artifact.

**Verification is not succinct in any useful sense.** The folded instance is checked in tens of
seconds, and it degrades as the step circuit grows. Nothing here settles on-chain, which is the
motivation usually offered for proving inference at all.

**No paper, no review, no author list.** The repository states no authors; the acknowledgements
name advisors, not contributors. We record the attribution as unverified in `papers.yml` and you
should cite the project, not a person, unless you can confirm it independently. Treat every
figure on this page the way you would treat a benchmark in a blog post, because that is what it
is.
