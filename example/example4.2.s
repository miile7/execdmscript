// @execdmscript.ignore.start

// all the code here will never be executed except this
// dm-script code is executed manually
string variable1 = "Test";
number variable2 = 1;
result("This will not be printed when executed via python.\n")

// @execdmscript.ignore.end

result(variable1 + "\n");
result(variable2 + "\n");

// @execdmscript.ignore.start
result("Ignored again")
// @execdmscript.ignore.end
