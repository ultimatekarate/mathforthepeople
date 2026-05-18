---
title: What are numbers and how do they work?
author: joe
date: 2026-05-14
slug: numbers-how
draft: false
---
For most of us, our first exposure to mathematics is counting. How many of the thing do I have? How many minutes do I have to play? I don't want four grapes, I want five. We're born with an inherent sense of quantity. We know when something is big. We can visually assess when there is more or less of something. That's _quantity_. There is a difference between quantity and numbers. Numbers are things that we use to describe quantities.[^1] Don't get me wrong. Using number to describe a physical quantity is immensely useful, but things really become interesting when you learn to separate the two ideas entirely.

## The Natural Numbers and Counting

Let us begin at the beginning. The natural numbers, denoted by $\mathbb{N}$, or whole numbers: 0, 1, 2, 3, and so on.[^2] The natural numbers have many nice properties. My favorite is closure under addition. We say a set $\set{S}$ is closed under addition if for any $n_1,n_2 \in \mathbb{N}$ then the sum, $n_1+n_2$, is also a natural number.

It's convenient to include 0 in the natural numbers because it is the _additive identity_. That means $n + 0 = n$ for every $n \in \mathbb{N}$, adding 0 to another number.

## The Integers, Addition, and Subtraction

Now, what if we combine this notion of additive identity and closure under addition? What are the natural numbers, $n_1,n_2$ that satisfy the equation $n_1 + n_2 = 0$? Trivially, we see that $n_1 = n_2 = 0$, is a solution. But are there any others? Suppose $n_1=6781123496789$, that's a natural number. Does there exist a natural number $n_2$ such that $6781123496789 + n_2 = 0$? No. You need negative numbers to do this, which is impossible if you can't divorce the notion of quantity from number. This actually [happened](https://en.wikipedia.org/wiki/Negative_number#History). Solutions that involved negative numbers were considered false or absurd.

At some point some nerd decided that it might be useful to consider what negative numbers might have to offer us. Thus, the integers, $\mathbb{Z}$, showed up.[^4] The integers have the property that for any $z\in\mathbb{Z}$ there exists a _unique_ $z_* \in \mathbb{Z}$ such that $z+z_* = 0.$ When this happens, we say that $z_*$ is the _additive inverse_ of $z.$ It should be pretty clear that the natural numbers are a subset of the integers. We denote this by $\mathbb{N} \subset \mathbb{Z}$.

Notice that we haven't mentioned subtraction once. We are thinking purely in terms of addition. It is tempting to think about subtraction as addition of a negative number. It is not. $a + (-b) = (-b) + a$. That is true because addition commutes. It is not true that $a-b=b-a$. Subtraction does not commute.

## The Rational Numbers, Multiplication, and Division

 The rational numbers arise from the integers when you ask the same question about multiplication as we did addition.[^3] It's pretty clear that for any two integers $z_1, z_2 \in \mathbb{Z}$ that $z_1 \cdot z_2 \in \mathbb{Z}.$ It's also pretty clear that $z\cdot 1=z$ for every $z\in\mathbb{Z}$. This makes 1 the _multiplicative identity_.

 Now we ask ourselves for a given $z \in \mathbb{Z}$, $z\neq 0$, does there exist a unique $z_*$ such that $z\cdot z_* = 1?$ If such a $z_*$ exists, we say it is the _multiplicative inverse_ of $z$. It's true for 1 and -1, but what the remaining integers? How do we know this?

 Since $z\neq 0$, we know that $|z|>0$. We can assume, without loss of generality, that $z>1.$ Well, since $z>1$ it must be the case that $z_* = \tfrac{1}{z} < 1$. Since $z>0$, we also know that $z_* > 0$. Thus, $0 < z_* < 1$. Uh oh, there aren't any integers in between 0 and 1. We're going to need more numbers.

 We say a number $q \in \mathbb{Q}$ is _rational_ if there exist two integers $p,r \in \mathbb{Z}$ such that $q=p/r.$ That's it. The rational numbers are also numbers whose decimal representation is either finite or repeating. Where the integers gave us closure under addition, the rationals get us to closure under multiplication.

Notice again, that we're just talking in terms of multiplication and not division. It is tempting to think of division as multiplying by a reciprocal. It is true that $a\cdot \tfrac{1}{b} = \tfrac{1}{b} \cdot a$, for $a,b \in \mathbb{Q}$, but it is not always true that $a/b = b / a.$ Division does not commute.

### Division by zero

Why can't you divide by zero? Well, you can, it's just nonsense. Don't think about it in terms of quantity. Think about it in terms of number. Consider the following $1 \cdot 0 = 2 \cdot 0.$ Suppose I divide both left and right hand side by 0. I'm left with $1=2$, it's very obviously false. The problem with division by 0 isn't with division by 0. The problem is with multiplication by 0. If I start at 2 and decide I want to go to 5, I can get there many ways. I could add 3. I could multiply by $\tfrac{5}{2}$. If want to get back to 2 I could subtract 3 or divide by $\tfrac{5}{2}$. Algebraically, I'm applying an operation followed immediately by its inverse.

Multiplying by 0 is not invertible, meaning that you can't get back to where you started. Invertible operations leave directions telling you how to get back home. A non-invertible operation let's you go someplace but it forces you to throw away the map you used to get their once you arrive.

## And then there were the Real numbers

A full treatment of the construction of the real numbers is exhausting, so I'm going to wave my hands a bit here.

The real numbers, $\mathbb{R}$, are what you get when you ask "Are there numbers that cannot be written as a ratio of two integers?" The numbers that have this property are called _irrational numbers_. How do we know that such a number exists? I claim that $\sqrt{2}$ is irrational. The standard proof is by contradiction. 

Assume that $\sqrt{2}$ is rational. Thus, $\sqrt{2} = \tfrac{a}{b},$ for some $a,b \in \mathbb{Z}$ where $a,b$ do not share any prime factors. This is to say $\tfrac{a}{b}$ is in simplest form. Squaring both sides of the equation yields $2 = \tfrac{a^2}{b^2}$. Applying a bit of algebra, we note that $2b^2=a^2$. This implies that $a^2$ is an even number. If $a^2$ is even, then $a$ must be even. So, $a=2c$, for some $c\in\mathbb{Z}$. We know that $$2b^2=a^2 = (2c)^2 = 4c^2.$$ 

Dividing through by 2 yields $b^2 = 2c^2$, so $b$ must also be even. Thus, $b = 2d$ for some $d \in \mathbb{Z}$. This violates our assumption that $\tfrac{a}{b}$ was in simplest form. This is a contradiction. Therefore, $\sqrt{2}$ cannot be rational.

There you have it, there exists at least one irrational number.

## In closing

The ideas discussed in this post are simple and familiar to most, but just because something is simple and familiar doesn't mean we can't think deeply about them. Numbers don't just exist in a vacuum. They have structure. They have gaps. This whole post was an exercise in examining those gaps and seeing where they might lead.

We started with counting and natural numbers. We ended up with a subset chain $\mathbb{N} \subset \mathbb{Z} \subset\mathbb{Q} \subset\mathbb{R}$ where each link was formed by asking some variation of "What if ...?" An observant reader will notice that I have not mentioned the complex numbers. They will get their own post in the near future.

[^1]: IAoFF: I'm fully aware of the set theoretic definition of natural numbers, equivalence classes, and Dedekind cuts. We're building intuitive scaffolding here, not trying to scare people away. I see you though, number theorists. I appreciate your work.
[^2]: There are some folks who will say that 0 is not a natural number. Those folks are called assholes.
[^3]: Interestingly, the existence of rational numbers was never really disputed. Euclid very clearly understood the concept of ratio.
[^4]: We use $\mathbb{Z}$ because of the German word _z&auml;hlen_ which translates to "count" in English.