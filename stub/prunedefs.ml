open Cil;;
module StringSet = Set.Make (String);;

exception ContainsWhitespace of string;;
exception UnhandledType of string;;
exception Exception of string;;


(* hurrah for type systems and no reflection or metaprogramming *)
let rec stringifyType (t : typ) :string = 
    match t with
        TVoid(_) -> "void"
    |   TInt(IChar, _) -> "char"
    |   TInt(ISChar, _) -> "signed char"	
    |   TInt(IUChar, _) -> "unsigned char"
    |   TInt(IInt, _) -> "int"
    |   TInt(IUInt, _) -> "unsigned int"
    |   TInt(IShort, _) -> "short"
    |   TInt(IUShort, _) -> "unsigned short"
    |   TInt(ILong, _) -> "long"
    |   TInt(IULong, _) -> "unsigned long"
    |   TInt(ILongLong, _) -> "long long"
    |   TInt(IULongLong, _) -> "unsignd long long"
    |   TFloat(FFloat, _) -> "float"
    |   TFloat(FDouble, _) -> "double"
    |   TFloat(FLongDouble, _) -> "long double"
    |   TPtr(t, _) ->  stringifyType(t) ^ "*"
    |   TArray(t, Some Const(CInt64(length, _, __)), _) -> stringifyType(t) ^ (Printf.sprintf "[%Ld]" length)
    |   TArray(t, _, __) -> raise (UnhandledType (stringifyType(t) ^ "of non constant (or weird-constant) length"))
    |   TFun(_, __, ___, ____) -> raise (UnhandledType "TFun")
    |   TNamed(_, __) -> raise (UnhandledType "TNamed (i.e typedef)")
    |   TComp(_, __) -> raise (UnhandledType "TComp (composite)")
    |   TEnum(_, __) -> raise (UnhandledType "Enum ")
    |   TBuiltin_va_list(_) -> "..."
;;

let getArgSpec (func) =
    let returnType = match func.svar.vtype with
        TFun(t, _, __, ____) -> stringifyType t
        | t -> raise (Exception "really broken") in
    Printf.sprintf "%s %s(%s)"
        returnType 
        func.svar.vname 
        ( String.concat ", " (
          List.map (function info -> stringifyType info.vtype) func.sformals));;

let prunees = ref StringSet.empty;;
let collectPrunees (filename) = begin
    let channel = open_in filename in
    try
        while true do
            let line = input_line channel in
            if String.contains line ' ' then raise (ContainsWhitespace line);
            prunees := StringSet.add line !prunees
         done
    with End_of_file -> close_in channel
end;;

let specFile = ref "";;
let setSpecFile (filename) = 
    specFile := filename;;
  
let appendToFile (s: string) = 
    let channel = open_out_gen [Open_creat; Open_append] 0o644 !specFile in
    output_string channel s;
    output_string channel "\n";
    close_out channel

let shouldPrune (g : global) : bool = 
    match g with
        GFun(f, l) when StringSet.mem f.svar.vname !prunees -> 
            if (!specFile <> "") then appendToFile (getArgSpec f);
            true
    |   GVar(v, i, l) when StringSet.mem v.vname !prunees -> true
    |   g -> false;;


class definitionPruner : cilVisitor = object(self)
    inherit nopCilVisitor
  
    method vglob (g : global) =
      if shouldPrune g then
          ChangeTo []
      else
          SkipChildren
end;;

let pruneDefs (f : file) : unit =
    visitCilFile (new definitionPruner) f

let feature : featureDescr = 
  { fd_name = "prunedefs";
    fd_enabled = ref false;
    fd_description = "strip various global definitions";
    fd_extraopt = [
        ("--prunedefs", 
             Arg.String collectPrunees, 
             " the file containing symbols which should be pruned");
        ("--specfile", 
             Arg.String setSpecFile,
             " the file to which argument specs should be appended");];
    fd_doit = pruneDefs;
    fd_post_check = false}
