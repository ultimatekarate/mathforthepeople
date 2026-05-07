---
title: How I Made Two Dollars Out of One Using Math
author: dipshit
date: 2026-04-22
slug: two-from-one
---

I have been reading my colleague Dr. Joe's post on the [[?geometric-series]],
in particular the formula derived in
[[geometric-series#eq:geometric|equation 1 of his post]], and I have noticed
something he failed to point out, which is that I can use it to print money.

Observe. Take one dollar. Spend half of it. You now have fifty cents and a
sandwich. Spend half of *that*. You now have twenty-five cents and one and
a half sandwiches, because the second sandwich is half a sandwich. Continue
in this fashion. By [[geometric-series]], the total amount of sandwich you
will accumulate is

$$ \sum_{n=1}^{\infty} \frac{1}{2^n} = 1 $$

a whole sandwich, on top of the half-sandwich you started with, for a grand
total of one and a half sandwiches from one dollar. The sandwich is worth
fifty cents. So I have turned one dollar into one dollar and a half,
spendable money plus sandwich-equivalent.

Repeat the procedure with the dollar fifty. You now have two dollars and a
quarter. Repeat again. You now have three dollars and thirty-seven cents.
Apply the geometric series to the *number of times you have applied the
geometric series* and the total approaches infinity. By
[[?convergence|convergent reasoning]], I am going to be very rich.

I have been informed by [Dr. Joe](/joe/) that this is "not how money works"
and "not how sandwiches work" and "please stop emailing the dean about
this." I will be ignoring his concerns. The mathematics is correct. The
mathematics is always correct.

---

*Dr. Dipshit's posts are not peer-reviewed and should not be used as the
basis for any financial decision, sandwich-related or otherwise.*
