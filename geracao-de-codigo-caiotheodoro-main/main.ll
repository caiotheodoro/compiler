; ModuleID = "main.bc"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

declare void @"w_int_var"(i32 %".1")

declare void @"w_float_var"(float %".1")

declare i32 @"r_int_var"()

declare float @"r_float_var"()

define i32 @"main"()
{
entry:
  %"x" = alloca i32, align 4
  %"y" = alloca float, align 4
  store float              0x0, float* %"y"
  store i32 0, i32* %"x"
  store float              0x0, float* %"y"
  %".5" = call i32 @"r_int_var"()
  store i32 %".5", i32* %"x", align 4
  %".7" = call float @"r_float_var"()
  store float %".7", float* %"y", align 4
  %".9" = load float, float* %"y"
  call void @"w_float_var"(float %".9")
  br label %"exit"
exit:
  %"z" = alloca i32, align 4
}
