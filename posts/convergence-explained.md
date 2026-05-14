---
title: What "Converges" Actually Means
author: joe
date: 2026-04-18
slug: convergence-explained
draft: false
---

The notion of convergence is absolutely fundamental in mathematics. 

## The picture

Imagine a sequence of numbers — say,

$$ 0.9,\ 0.99,\ 0.999,\ 0.9999,\ \ldots $$

Each one is closer to $1$ than the last. None of them is $1$. But if I
ask "is the sequence settling on something?" you'd say yes, obviously, it's
settling on $1$. That intuition — the sequence is heading somewhere, even
if it never lands — is what convergence formalizes.

## The promise

Here's the precise version. A sequence $a_1, a_2, a_3, \ldots, a_n$ *converges
to $L$* if, for any tolerance you can name — call it $\varepsilon$, no
matter how small — the sequence eventually gets within $\varepsilon$ of
$L$, and stays there.

That last clause does the heavy lifting. "Eventually" means: there's some
position $N$ in the sequence past which everything is within $\varepsilon$
of $L$. *Once you're close, you stay close.* Written precisely, it looks like this: 

$$|a_n - L| \leq \varepsilon, N \leq n.$$

Convergence isn't about getting to $L$; it's about a binding promise that the wandering stops. We actually don't care if the sequence ever reaches $L$. Convergence is a weaker version of equality.

It's worth noting that this is a [[?partial-sum|partial-sum-style]]
argument when applied to series: a series $\sum a_n$ converges if its
partial sums form a sequence that converges in the sense above.

## A concrete example

The walking-distance argument from [[geometric-series]] is the simplest
case. It is pretty straightforward to compute the first five partial sums

$$ 1,\ \tfrac{3}{2},\ \tfrac{7}{4},\ \tfrac{15}{8},\ \tfrac{31}{16}.$$

By inspection, one can see a pattern starting to form, i.e. the $n^{th}$ partial sum is $g_n = \tfrac{2^{n+1}-1}{2^n}$. The important thing to notice here is that the 1 in the numerator is a constant. As $n$ gets very large, that 1 is going to become arbitrarily small relative to $2^{n+1}$. A bit of algebra yields 

$$g_n = \tfrac{2^{n+1}-1}{2^n} = \tfrac{2^{n+1}}{2^n}-\tfrac{1}{2^n} = 2 - \tfrac{1}{2^n}.$$ 

As $n$ grows larger, we subtract increasingly smaller numbers from 2. That's convergence.

Compare with the series $$D_n = \sum_{k=0}^n 2^k = 1 + 2 + 4 \ldots + 2^n.$$ Its partial sums grow without bound. There's no $L$ that the partial sums settle near, no
matter how generous a tolerance you allow. That series *diverges*. Why do we care about this distinction? Suppose $D_n$ did converge to some $D$. 

$$D = 1 + \underbrace{2 + 4 + 8 + \ldots}_{2D}$$

$$D = 1 + 2D$$

$$D = -1$$

This is very clearly nonsense. $D$ is the sum of positive numbers. This is why convergence matters.

## Why the definition is shaped this way

The definition for convergence may seem fiddly and dumb, but there's a reason for it. It's because it shows up all over the place. There are only so many good ideas in math and mathematicians figured out pretty early on that you should just reuse them wherever you can. When something is so ubiquitous the definition for it _must_ be air tight.
