import sys
from pathlib import Path

MAT1, MAT2, TMAT, MASK, K = -1888480786, -59179233, 932445695, 2147483647, 1812433253
LANES = (("", 0), ("b", 4))
INIT_ORDER = (("$s1", "$s0"), ("$s2", "$s1"), ("$s3", "$s2"), ("$s0", "$s3"), ("$s1", "$s0"), ("$s2", "$s1"), ("$s3", "$s2"))


def v_init(i, dst, src, z):
    d, s = dst + z, src + z
    return f"""
        (local.set {d} (v128.xor (local.get {d}) (i32x4.add (i32x4.splat (i32.const {i})) (i32x4.mul (global.get $vk) (v128.xor (local.get {s}) (i32x4.shr_u (local.get {s}) (i32.const 30)))))))"""


def v_certify(z):
    return f"""
        (local.set $z (i32x4.eq (v128.or (v128.or (v128.and (local.get $s0{z}) (global.get $vmask)) (local.get $s1{z})) (v128.or (local.get $s2{z}) (local.get $s3{z}))) (v128.const i32x4 0 0 0 0)))
        (if (v128.any_true (local.get $z))
          (then
            (local.set $s0{z} (v128.bitselect (v128.const i32x4 84 84 84 84) (local.get $s0{z}) (local.get $z)))
            (local.set $s1{z} (v128.bitselect (v128.const i32x4 73 73 73 73) (local.get $s1{z}) (local.get $z)))
            (local.set $s2{z} (v128.bitselect (v128.const i32x4 78 78 78 78) (local.get $s2{z}) (local.get $z)))
            (local.set $s3{z} (v128.bitselect (v128.const i32x4 89 89 89 89) (local.get $s3{z}) (local.get $z)))))"""


def v_step(z):
    return f"""
        (local.set $x{z} (v128.xor (v128.xor (v128.and (local.get $s0{z}) (global.get $vmask)) (local.get $s1{z})) (local.get $s2{z})))
        (local.set $x{z} (v128.xor (local.get $x{z}) (i32x4.shl (local.get $x{z}) (i32.const 1))))
        (local.set $y{z} (v128.xor (v128.xor (local.get $s3{z}) (i32x4.shr_u (local.get $s3{z}) (i32.const 1))) (local.get $x{z})))
        (local.set $m{z} (i32x4.neg (v128.and (local.get $y{z}) (global.get $vone))))
        (local.set $s0{z} (local.get $s1{z}))
        (local.set $s1{z} (v128.xor (local.get $s2{z}) (v128.and (local.get $m{z}) (global.get $vmat1))))
        (local.set $s2{z} (v128.xor (v128.xor (local.get $x{z}) (i32x4.shl (local.get $y{z}) (i32.const 10))) (v128.and (local.get $m{z}) (global.get $vmat2))))
        (local.set $s3{z} (local.get $y{z}))"""


def v_temper(z):
    return f"""
        (local.set $x{z} (i32x4.add (local.get $s0{z}) (i32x4.shr_u (local.get $s2{z}) (i32.const 8))))
        (local.set $o{z} (v128.xor (v128.xor (local.get $s3{z}) (local.get $x{z})) (v128.and (i32x4.neg (v128.and (local.get $x{z}) (global.get $vone))) (global.get $vtmat))))"""


def v_lane(k, z, base):
    return f"""
        (local.set $out (i32x4.extract_lane {k} (local.get $o{z})))
        (local.set $r (i32.sub (local.get $out) (i32.mul (i32.trunc_sat_f64_u (f64.mul (f64.convert_i32_u (local.get $out)) (global.get $inv))) (global.get $g4))))
        (if (i32.ge_u (local.get $r) (global.get $g4)) (then (local.set $r (i32.sub (local.get $r) (global.get $g4)))))
        (local.set $t (i32.load8_u offset=512 (local.get $r)))
        (if (i32.load8_u offset=4096 (local.get $t))
          (then
            (if (call $tail (local.get $t) (i32x4.extract_lane {k} (local.get $s0{z})) (i32x4.extract_lane {k} (local.get $s1{z})) (i32x4.extract_lane {k} (local.get $s2{z})) (i32x4.extract_lane {k} (local.get $s3{z})))
              (then
                (i32.store offset=16384 (i32.shl (global.get $hits) (i32.const 2)) (i32.add (local.get $start) (i32.add (local.get $i) (i32.const {base + k}))))
                (global.set $hits (i32.add (global.get $hits) (i32.const 1)))
                (if (i32.ge_u (global.get $hits) (local.get $max))
                  (then (return (i32.add (local.get $i) (i32.const {base + k + 1})))))))))"""


def s_step():
    return f"""
        (local.set $x (i32.xor (i32.xor (i32.and (local.get $a) (i32.const {MASK})) (local.get $b)) (local.get $c)))
        (local.set $x (i32.xor (local.get $x) (i32.shl (local.get $x) (i32.const 1))))
        (local.set $y (i32.xor (i32.xor (local.get $d) (i32.shr_u (local.get $d) (i32.const 1))) (local.get $x)))
        (local.set $m (i32.sub (i32.const 0) (i32.and (local.get $y) (i32.const 1))))
        (local.set $a (local.get $b))
        (local.set $b (i32.xor (local.get $c) (i32.and (local.get $m) (i32.const {MAT1}))))
        (local.set $c (i32.xor (i32.xor (local.get $x) (i32.shl (local.get $y) (i32.const 10))) (i32.and (local.get $m) (i32.const {MAT2}))))
        (local.set $d (local.get $y))"""


def s_steps(count, label):
    return f"""
      (local.set $k {count})
      (loop ${label}{s_step()}
        (local.set $k (i32.sub (local.get $k) (i32.const 1)))
        (br_if ${label} (local.get $k)))"""


def s_temper():
    return f"""
      (local.set $x (i32.add (local.get $a) (i32.shr_u (local.get $c) (i32.const 8))))
      (local.set $o (i32.xor (i32.xor (local.get $d) (local.get $x)) (i32.and (i32.sub (i32.const 0) (i32.and (local.get $x) (i32.const 1))) (i32.const {TMAT}))))"""


def s_init(i, dst, src):
    return f"""
    (local.set {dst} (i32.xor (local.get {dst}) (i32.add (i32.const {i}) (i32.mul (i32.const {K}) (i32.xor (local.get {src}) (i32.shr_u (local.get {src}) (i32.const 30)))))))"""


def header():
    return f"""
(module
  (memory (export "memory") 2)
  (global $g4 (mut i32) (i32.const 0))
  (global $g5 (mut i32) (i32.const 0))
  (global $g6 (mut i32) (i32.const 111))
  (global $g7 (mut i32) (i32.const 20))
  (global $inv (mut f64) (f64.const 0))
  (global $hits (export "hits") (mut i32) (i32.const 0))
  (global $vmask v128 (v128.const i32x4 {MASK} {MASK} {MASK} {MASK}))
  (global $vone v128 (v128.const i32x4 1 1 1 1))
  (global $vmat1 v128 (v128.const i32x4 {MAT1} {MAT1} {MAT1} {MAT1}))
  (global $vmat2 v128 (v128.const i32x4 {MAT2} {MAT2} {MAT2} {MAT2}))
  (global $vtmat v128 (v128.const i32x4 {TMAT} {TMAT} {TMAT} {TMAT}))
  (global $vk v128 (v128.const i32x4 {K} {K} {K} {K}))
  (func (export "patterns") (param i32 i32) (global.set $g6 (local.get 0)) (global.set $g7 (local.get 1)))
  (func (export "configure") (param i32 i32)
    (local $t i32) (local $acc i32)
    (global.set $g4 (local.get 0))
    (global.set $g5 (local.get 1))
    (global.set $inv (f64.div (f64.const 1) (f64.convert_i32_u (local.get 0))))
    (loop $c
      (i32.store offset=24576 (i32.shl (local.get $t) (i32.const 2)) (local.get $acc))
      (local.set $acc (i32.add (local.get $acc) (i32.load (i32.shl (local.get $t) (i32.const 2)))))
      (local.set $t (i32.add (local.get $t) (i32.const 1)))
      (br_if $c (i32.lt_u (local.get $t) (i32.const 79)))))"""


def tail():
    return f"""
  (func $tail (param $t i32) (param $a i32) (param $b i32) (param $c i32) (param $d i32) (result i32)
    (local $n i32) (local $total i32) (local $p i32) (local $r i32) (local $w i32) (local $j i32) (local $k i32)
    (local $x i32) (local $y i32) (local $m i32) (local $o i32)
    (local.set $total (global.get $g4))
    (loop $main
      (local.set $j (local.get $n))
      (block $placed
        (loop $shift_up
          (br_if $placed (i32.eqz (local.get $j)))
          (local.set $w (i32.load8_u offset=6499 (local.get $j)))
          (br_if $placed (i32.lt_u (local.get $w) (local.get $t)))
          (i32.store8 offset=6500 (local.get $j) (local.get $w))
          (local.set $j (i32.sub (local.get $j) (i32.const 1)))
          (br $shift_up)))
      (i32.store8 offset=6500 (local.get $j) (local.get $t))
      (local.set $n (i32.add (local.get $n) (i32.const 1)))
      (if (i32.ge_u (local.get $n) (global.get $g5)) (then (return (i32.const 1))))
      (local.set $total (i32.sub (local.get $total) (i32.load (i32.shl (local.get $t) (i32.const 2)))))
      {s_steps("(i32.const 7)", "adv7")}
      {s_temper()}
      (local.set $p (i32.rem_u (local.get $o) (global.get $g6)))
      {s_steps("(select (i32.const 1) (i32.const 2) (i32.load8_u offset=6000 (local.get $t)))", "adv12")}
      (if (i32.ge_u (local.get $p) (global.get $g7)) (then {s_steps("(i32.const 2)", "adv2")}))
      {s_steps("(i32.const 5)", "adv5")}
      {s_temper()}
      (local.set $r (i32.rem_u (local.get $o) (local.get $total)))
      (local.set $j (i32.const 0))
      (block $mapped
        (loop $skip
          (br_if $mapped (i32.ge_u (local.get $j) (local.get $n)))
          (local.set $w (i32.load8_u offset=6500 (local.get $j)))
          (br_if $mapped (i32.gt_u (i32.load offset=24576 (i32.shl (local.get $w) (i32.const 2))) (local.get $r)))
          (local.set $r (i32.add (local.get $r) (i32.load (i32.shl (local.get $w) (i32.const 2)))))
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $skip)))
      (local.set $t (i32.load8_u offset=512 (local.get $r)))
      (br_if $main (i32.load8_u offset=4096 (i32.add (i32.mul (local.get $n) (i32.const 79)) (local.get $t)))))
    (i32.const 0))"""


def match():
    body = f"""
  (func $match (param $seed i32) (result i32)
    (local $s0 i32) (local $s1 i32) (local $s2 i32) (local $s3 i32)
    (local $a i32) (local $b i32) (local $c i32) (local $d i32) (local $x i32) (local $y i32) (local $m i32) (local $o i32) (local $k i32) (local $t i32)
    (local.set $s0 (local.get $seed))
    (local.set $s1 (i32.const {MAT1}))
    (local.set $s2 (i32.const {MAT2}))
    (local.set $s3 (i32.const {TMAT}))"""
    for i, (d, s) in enumerate(INIT_ORDER, 1):
        body += s_init(i, d, s)
    body += f"""
    (if (i32.eqz (i32.or (i32.or (i32.and (local.get $s0) (i32.const {MASK})) (local.get $s1)) (i32.or (local.get $s2) (local.get $s3))))
      (then (local.set $s0 (i32.const 84)) (local.set $s1 (i32.const 73)) (local.set $s2 (i32.const 78)) (local.set $s3 (i32.const 89))))
    (local.set $a (local.get $s0))
    (local.set $b (local.get $s1))
    (local.set $c (local.get $s2))
    (local.set $d (local.get $s3))
    {s_steps("(i32.const 9)", "warm")}
    {s_temper()}
    (local.set $t (i32.load8_u offset=512 (i32.rem_u (local.get $o) (global.get $g4))))
    (if (i32.eqz (i32.load8_u offset=4096 (local.get $t))) (then (return (i32.const 0))))
    (call $tail (local.get $t) (local.get $a) (local.get $b) (local.get $c) (local.get $d)))
  (func $scan1 (param $start i32) (param $i i32) (param $count i32) (param $max i32) (result i32)
    (block $done
      (loop $each
        (br_if $done (i32.ge_u (local.get $i) (local.get $count)))
        (if (call $match (i32.add (local.get $start) (local.get $i)))
          (then
            (i32.store offset=16384 (i32.shl (global.get $hits) (i32.const 2)) (i32.add (local.get $start) (local.get $i)))
            (global.set $hits (i32.add (global.get $hits) (i32.const 1)))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br_if $done (i32.ge_u (global.get $hits) (local.get $max)))
        (br $each)))
    (local.get $i))"""
    return body


def scan():
    out = """
  (func (export "scan") (param $start i32) (param $count i32) (param $max i32) (result i32)
    (local $i i32) (local $out i32) (local $t i32) (local $limit i32) (local $r i32) (local $z v128)
    (local $s0 v128) (local $s1 v128) (local $s2 v128) (local $s3 v128) (local $x v128) (local $y v128) (local $m v128) (local $o v128)
    (local $s0b v128) (local $s1b v128) (local $s2b v128) (local $s3b v128) (local $xb v128) (local $yb v128) (local $mb v128) (local $ob v128)
    (global.set $hits (i32.const 0))
    (if (i32.or (i32.eqz (local.get $max)) (i32.eqz (global.get $g4)))
      (then (return (call $scan1 (local.get $start) (i32.const 0) (local.get $count) (local.get $max)))))
    (local.set $limit (i32.and (local.get $count) (i32.const -8)))
    (block $done
      (loop $group
        (br_if $done (i32.ge_u (local.get $i) (local.get $limit)))"""
    for z, off in LANES:
        out += f"""
        (local.set $s0{z} (i32x4.add (i32x4.splat (i32.add (local.get $start) (local.get $i))) (v128.const i32x4 {off} {off + 1} {off + 2} {off + 3})))
        (local.set $s1{z} (global.get $vmat1))
        (local.set $s2{z} (global.get $vmat2))
        (local.set $s3{z} (global.get $vtmat))"""
    for i, (d, s) in enumerate(INIT_ORDER, 1):
        for z, _ in LANES:
            out += v_init(i, d, s, z)
    for z, _ in LANES:
        out += v_certify(z)
    for _ in range(9):
        for z, _ in LANES:
            out += v_step(z)
    for z, _ in LANES:
        out += v_temper(z)
    for z, base in LANES:
        for k in range(4):
            out += v_lane(k, z, base)
    out += """
        (local.set $i (i32.add (local.get $i) (i32.const 8)))
        (br $group)))
    (call $scan1 (local.get $start) (local.get $i) (local.get $count) (local.get $max)))"""
    return out


def module():
    return header() + tail() + match() + scan() + "\n)\n"


if __name__ == "__main__":
    Path(sys.argv[1]).write_text(module())
