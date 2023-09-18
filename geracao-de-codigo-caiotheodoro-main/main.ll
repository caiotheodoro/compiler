; ModuleID = "main.bc"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

declare void @"w_int_var"(i32 %".1")

declare void @"w_float_var"(float %".1")

declare i32 @"r_int_var"()

declare float @"r_float_var"()

@"a" = common global i32 0, align 4
define i32 @"main"()
{
entry:
  %"ret" = alloca i32, align 4
  store i32 10, i32* @"a"
  %".3" = load i32, i32* @"a"
  %".4" = icmp sgt i32 %".3", 5
  br %".4" = icmp sgt i32 %".3", 5 %".4" = icmp sgt i32 %".3", 5, %"iftrue_1" = iftrue_1:
  store i32 1, i32* %"ret"
  br %"ifend1" = ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"ifend1" = ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"iftrue_1" = iftrue_1:
  store i32 1, i32* %"ret"
  br %"ifend1" = ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"ifend1" = ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11", %"iffalse_1" = iffalse_1:
  store i32 0, i32* %"ret"
  br %"ifend1" = ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"ifend1" = ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"iffalse_1" = iffalse_1:
  store i32 0, i32* %"ret"
  br %"ifend1" = ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"ifend1" = ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11"
exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11"
iftrue_1:
  store i32 1, i32* %"ret"
  br %"ifend1" = ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"ifend1" = ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11"
iffalse_1:
  store i32 0, i32* %"ret"
  br %"ifend1" = ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"ifend1" = ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11"
ifend1:
  br %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11" %"exit" = exit:
  %".11" = load i32, i32* %"ret"
  ret i32 %".11"
}
