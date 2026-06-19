// Lab 10: Formal Verification with Dafny

// Exercise 1: Absolute Value
method Abs(x: int) returns (y: int)
  ensures y >= 0
  ensures y == x || y == -x
{
  if x >= 0 {
    y := x;
  } else {
    y := -x;
  }
}

// Exercise 2: Max
method Max(x: int, y: int) returns (m: int)
  ensures m >= x && m >= y
  ensures m == x || m == y
{
  if x >= y {
    m := x;
  } else {
    m := y;
  }
}

// Exercise 3: Strengthen the Specification
method MaxWeakFixed(x: int, y: int) returns (m: int)
  ensures m >= x && m >= y
  // Fix: Strengthen the spec so that the bogus implementation is rejected
  ensures m == x || m == y
{
  // This buggy implementation will now be rejected by the compiler:
  // m := x + y + 1;
  
  // Correct implementation to satisfy the strengthened specification:
  if x >= y {
    m := x;
  } else {
    m := y;
  }
}

// Exercise 4: Specify the Bank Transfer
method TransferSpec(a: int, b: int, amount: int) returns (a2: int, b2: int)
  // Preconditions:
  // - Validity: neither balance goes negative (requires starting non-negative and transferring at most the balance)
  requires a >= 0 && b >= 0
  requires a >= amount
  // - Direction: amount must be strictly positive
  requires amount > 0
  
  // Postconditions:
  // - Conservation: total money is preserved
  ensures a2 + b2 == a + b
  // - Exact transfer details
  ensures a2 == a - amount
  ensures b2 == b + amount
  // - Post-condition validity
  ensures a2 >= 0 && b2 >= 0
{
  a2 := a - amount;
  b2 := b + amount;
}

// Exercise 5: Unsafe Access (Omitted precondition to observe compiler error)
// method GetAtUnsafe(arr: array<int>, i: int) returns (x: int)
// {
//   x := arr[i]; // Dafny reports: index out of range because i is unconstrained
// }

// Exercise 6: Add Loop Invariants to SumFixed
method SumFixed(n: int) returns (s: int)
  requires n >= 0
  ensures s == n * (n + 1) / 2
{
  s := 0;
  var i := 0;
  while i <= n
    // Invariants:
    // (a) Range invariant
    invariant 0 <= i <= n + 1
    // (b) Value invariant
    invariant s == i * (i - 1) / 2
  {
    s := s + i;
    i := i + 1;
  }
}

// Exercise 7: Max Array
method MaxArrayFixed(arr: array<int>) returns (m: int)
  requires arr.Length > 0
  ensures forall k :: 0 <= k < arr.Length ==> m >= arr[k]
{
  m := arr[0];
  var i := 1;
  while i < arr.Length
    // Invariants:
    // (a) Range invariant
    invariant 1 <= i <= arr.Length
    // (b) Maximality invariant over visited indices [0..i)
    invariant forall k :: 0 <= k < i ==> m >= arr[k]
  {
    if arr[i] > m {
      m := arr[i];
    }
    i := i + 1;
  }
}
