; ModuleID = "modulo_geracao_cod.bc"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

declare void @"escrevaInteiro"(i32 %".1")

declare void @"escrevaFlutuante"(float %".1")

declare i32 @"leiaInteiro"()

declare float @"leiaFlutuante"()

@"a" = common global i32 0, align 4
define i32 @"main"()
{
entry:
  %"b" = alloca i32, align 4
  store i32 10, i32* @"a"
  %".3" = load i32, i32* @"a"
  store i32 %".3", i32* %"b"
  br %"exit" = exit:
  %".6" = load i32, i32* %"b"
  ret i32 %".6" %"exit" = exit:
  %".6" = load i32, i32* %"b"
  ret i32 %".6"
exit:
  %".6" = load i32, i32* %"b"
  ret i32 %".6"
}
