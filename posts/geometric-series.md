---
title: Why the Geometric Series Adds Up
author: joe
date: 2026-04-15
slug: geometric-series
---

Suppose you take a step of length one, then half a step, then a quarter of a
step, and so on, halving each time. How far do you walk in total?

The honest answer is two, exactly two, and the surprise is not that it adds
up but that it adds up to something so clean. We're going to derive the
formula for an infinite [[?geometric-series]] carefully enough that, by the
end, the cleanness feels obvious.

## The setup

A *geometric series* is a sum where each term is a fixed multiple of the
previous one. If the first term is $a$ and the multiplier is $r$, the
series looks like

$$ a + ar + ar^2 + ar^3 + \cdots $$

Our walking example has $a = 1$ and $r = 1/2$. The condition we'll need
is that $|r| < 1$ — that is, each term is strictly smaller than the last
in absolute value. Without that, the terms don't shrink, and a sum of
non-shrinking terms can't [[?convergence|converge]] to anything.

## The trick

Let $S$ stand for the sum. Then

$$ S = a + ar + ar^2 + ar^3 + \cdots $$

Now multiply both sides by $r$:

$$ rS = ar + ar^2 + ar^3 + ar^4 + \cdots $$

Subtract the second equation from the first. Almost everything cancels —
every term on the right of the first equation, except $a$ itself, has a
twin on the right of the second:

$$ S - rS = a $$

Factor the left side and solve:

<div id="eq:geometric" class="equation">

$$ S = \frac{a}{1 - r} $$

</div>

That's the formula. For our walk, $a = 1$ and $r = 1/2$, so $S = 1/(1-1/2) = 2$.
The total distance is exactly two steps, no matter how many halvings you
chain together.

## A picture

It helps to see the [[?partial-sum|partial sums]] creeping up on their
[[?limit]]:

<script type="text/tikz">
\begin{tikzpicture}[scale=1.2]
  \draw[->, thick] (-0.3,0) -- (2.5,0) node[right] {$x$};
  \foreach \x/\lbl in {0/0, 1/1, 2/2}
    \draw (\x,0.08) -- (\x,-0.08) node[below] {$\lbl$};
  % Partial sums S_1=1, S_2=1.5, S_3=1.75, S_4=1.875, S_5=1.9375
  \foreach \x/\y in {1/0.4, 1.5/0.55, 1.75/0.7, 1.875/0.85, 1.9375/1.0} {
    \draw[red, thick] (\x,0.05) -- (\x,\y);
    \fill[red] (\x,\y) circle (1.5pt);
  }
  \draw[dashed] (2,0) -- (2,1.2) node[above] {limit};
\end{tikzpicture}
</script>

Each red dot is a partial sum. They get closer and closer to two but never
reach it — and yet the limit, the place they're heading, is a real and
exact number.

## Why this matters

The geometric series shows up everywhere: in compound interest, in the
analysis of algorithms, in the geometry of fractals, in probability when
you ask "how long until the first success?" Whenever you see a sum where
each term is a fixed fraction of the last, you can apply the formula
above without rederiving it.

It's also the simplest example of an infinite process that converges to
a finite answer, and learning to trust that intuition — that something
endless can still be bounded — is one of the small mental pivots that
calculus is built on.
