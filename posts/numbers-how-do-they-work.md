---
title: What are numbers and how do they work?
author: joe
date: 2026-05-14
slug: numbers-how
draft: true
---

For most of us, our first exposure to mathematics is counting. How many of the thing do I have? How many minutes do I have to play? I don't want four grapes, I want five. We're born with an inherent sense of quantity. We know when something is big. We can visually assess when there is more or less of something. That's _quantity_. There is a difference between quantity and numbers. Numbers are things that we use to describe quantities.[^1] Don't get me wrong. Using number to describe a physical quantity is immensely useful, but things really become interesting when you learn to separate the two ideas entirely. 

## What are numbers, really?
### The Natural Numbers
Let us begin at the beginning. The natural numbers, denoted by $\mathbb{N}$, or whole numbers: 0, 1, 2, 3, and so on.[^2] The natural numbers have many nice properties. My favorite is closure under addition. We say a set $\set{S}$ is closed under addition if for any $n_1,n_2 \in \mathbb{N}$ then the sum, $n_1+n_2$, is also a natural number.

It's convenient to include 0 in the natural numbers because it is the _additive identity_. That means $n + 0 = n$ for every $n \in \mathbb{N}$, adding 0 to another number. 

### And then there were the Integers
Now, what if we combine this notion of additive identity and closure under addition? What are the natural numbers, $n_1,n_2$ that satisfy the equation $n_1 + n_2 = 0$? Trivially, we see that $n_1 = n_2 = 0$, is a solution. But are there any others? Suppose $n_1=6781123496789$, that's a natural number. Does there exist a natural number $n_2$ such that $6781123496789 + n_2 = 0$? No. You need negative numbers to do this, which is impossible if you can't divorce the notion of quantity from number. This actually [happened](https://en.wikipedia.org/wiki/Negative_number#History). Solutions that involved negative numbers were considered false or absurd. 

Then the integers, $\mathbb{Z}$, showed up. Now you get something nice. The integers have the property that for any $z\in\mathbb{Z}$ there exists a UNIQUE $z_* \in \mathbb{Z}$ such that $z+z_* = 0.$ When this happens, we say that $z_*$ is the _additive inverse_ of $z.$ 

Notice that we haven't mentioned subtraction once. We are thinking purely in terms of addition. The integers arise from the naturals because of the a subtle interaction between closure under addition and the existence of an additive identity. 

### And then there were the Rational Numbers

The rational numbers, $\mathbb{Q}$, arise from the integers when you ask the same question about multiplication as we did addition.[^3] It's pretty clear that for any two integers $z_1, z_2 \in \mathbb{Z}$ that $z_1 \cdot z_2 \in \mathbb{Z},$ but what does there exist a unique $z_*$ such that for $z\cdot z_* = 1$? Again, no, but there does exist $q\in\mathbb{Q}$ such that $q=\tfrac{1}{z}=z_*$. The property of being a ratio of two integers is where the rational numbers get there name. We say a number $q$ is _rational_ if there exist two integers $p,r$ such that $q=p/r.$ That's it. The rational numbers are also numbers whose decimal representation is either finite or repeating.

### And then there were the Real numbers

The rational numbers are a subset of the real numbers. The remainder of the real numbers consist of the irrational numbers- numbers that cannot be expressed as a ratio of two integers. The irrational numbers are strange. Mostly because they're quite hard to construct outside of very specific examples like $e, \pi,$ and $\sqrt{2}$. There are also waaaaay more of them then there are rational numbers. 

"But, Joe, aren't both sets infinite? And infinity is always infinity, right?" Yes and no. It turns out there are infinitely infinities and only two of them are useful.

## Counting to $\infty$

But, how? What does it mean for infinite sets to be the same size? 


[^1]: IAoFF: I'm fully aware of the set theoretic definition of natural numbers, equivalence classes, and Dedekind cuts. We're building intuitive scaffolding here, not trying to scare people away. I see you though, number theorists. I appreciate your work.
[^2]: There are some folks who will say that 0 is not a natural number. Those folks are called assholes.
[^3]: Interestingly, the existence of rational numbers was never really disputed. Euclid talks about them at length.