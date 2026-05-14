---
title: Why the Geometric Series Adds Up
author: joe
date: 2026-04-15
slug: geometric-series
draft: false
technical: true
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

$$ S = a + ar + ar^2 + ar^3 + \cdots $$

Now, how do we know that $S$ is finite? Our walking example has $a = 1$ and $r = 1/2$. The condition we'll need
is that $|r| < 1$ — that is, each term is strictly smaller than the last
in absolute value. Without that, the terms don't shrink, and a sum of
non-shrinking terms can't [[?convergence|converge]] to anything. In fact, shrinking terms isn't enough to guarantee convergence.

## The trick

How does one compute an infinite sum in finite time? Well, you use a shortcut. Let $S$ stand for the sum. Then

$$ S_n = \Sigma_{k=0}^n ar^k $$

Now multiply both sides by $r$:

$$ rS_n = \Sigma_{k=0}^n ar^{k+1} $$

Subtract the second equation from the first. Almost everything cancels —
$$ S_n - rS_n = \Sigma_{k=0}^n ar^k - \Sigma_{k=0}^n ar^{k+1},$$

by combining sums we have
$$\Sigma_{k=1}^n \left(ar^k - ar^{k-1}\right) = a - ar^{n+1}.$$

Factor the left side and solve:

<div id="eq:geometric" class="equation">
$$ S_n = \frac{a(1-r^{n+1})}{1 - r},$$ 
</div>


since $|r|<1,$ it follows that $r^{n+1} \to 0$ as $n \to \infty$. So $$ S = \frac{a}{1 - r}.$$


That's the formula. For our walk, $a = 1$ and $r = 1/2$, so $S = 1/(1-1/2) = 2$.
The total distance is exactly two steps, no matter how many halvings you
chain together.

Notice that we're dividing by $1-r$. Remember earlier, the condition that $|r| <1$? Notice that as $r \to 1$ the denominator approaches 0, which implies $S \to \infty$.

## What happens when $|r|>1$?

Suppose, we let $r=2$. Then we get something like this:

<div id="eq:geometric-diverge" class="equation">

$$ S = \frac{a}{1 - 2} = -a = a + a/2 + a/4 + a/8 + \cdots $$

</div>

This is clearly nonsense for $a \neq 0$. If $a>0$, then $-a < 0$. The right hand side $$ a + a/2 + a/4 + a/8+ \cdots $$ is clearly the sum of positive numbers - it has no hope of being negative! The reason why it is nonsense is because the sum _diverges_ for $|r|>1.$ The summation formula we derived only makes sense when the sum _converges_.

## A picture

It helps to see the [[?partial-sum|partial sums]] creeping up on their
[[?limit]]:

<figure>
<script type="text/tikz">
\begin{tikzpicture}[scale=1.0]
  % Axes: n on the horizontal, S_n on the vertical.
  \draw[->, thick] (-0.3,0) -- (6.7,0) node[right] {$n$};
  \draw[->, thick] (0,-0.2) -- (0,2.5) node[above] {$S_n$};

  % Integer ticks on the n-axis, 1 through 6.
  \foreach \n in {1,2,3,4,5,6}
    \draw (\n,0.06) -- (\n,-0.06) node[below] {$\n$};

  % Reference ticks on the S_n axis at 1 and at the limit, 2.
  \foreach \y/\lbl in {1/1, 2/2}
    \draw (0.06,\y) -- (-0.06,\y) node[left] {$\lbl$};

  % Horizontal limit line at S_n = 2.
  \draw[dashed] (0,2) -- (6.5,2) node[right] {limit};

  % Connect the partial sums to make the climb toward the limit visible.
  % S_n = 2 - (1/2)^{n-1}
  \draw[red, thin]
    (1,1) -- (2,1.5) -- (3,1.75) -- (4,1.875) -- (5,1.9375) -- (6,1.96875);

  % Partial sum dots.
  \foreach \n/\val in {1/1, 2/1.5, 3/1.75, 4/1.875, 5/1.9375, 6/1.96875}
    \fill[red] (\n,\val) circle (1.7pt);
\end{tikzpicture}
</script>
<figcaption>Partial sums of the geometric series with $a = 1$ and $r = 1/2$</figcaption>
</figure>

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
