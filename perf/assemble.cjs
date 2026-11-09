const fs = require("fs");
require("wabt")().then((wabt) => {
  const [src, dst] = process.argv.slice(2);
  const mod = wabt.parseWat(src, fs.readFileSync(src, "utf8"), { simd: true });
  mod.validate();
  fs.writeFileSync(dst, Buffer.from(mod.toBinary({}).buffer));
  console.log("wrote " + dst + " (" + fs.statSync(dst).size + " bytes)");
});
