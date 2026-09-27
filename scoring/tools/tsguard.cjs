// What `editguard` is for `.py`, for `.ts`.
//
// THE FAILURE THIS EXISTS FOR, 2026-09-25. A regex edit to `enforce/native.ts`
// removed two entries from `NATIVE_BLOCKED` and left ORPHANED the continuation
// line of a third -- `'or only by prose. ...',` sitting alone inside an object
// literal. The file was broken; only `tsc` said so, and only because it was run
// by habit. On the python side `editguard.safe_write` refuses exactly this:
// a slice that takes more than it was aimed at.
//
// Goal K put real judgement on this side -- 25 rules, a transcription of
// CPython's `difflib.ratio`, the payload assemblers -- so the .ts files are now
// as load-bearing as the .py ones and were the only half without a guard.
//
// WHAT IT REFUSES, and each is a loss that PARSES and so reports nothing:
//   * an exported name that disappears undeclared;
//   * a key that disappears from a registry object (`RULES`, `NATIVE`,
//     `NATIVE_BLOCKED`) -- the tables this package dispatches on;
//   * text that no longer parses at all.
//
// It does NOT typecheck: that is `tsc`'s job and it is slow. This is the cheap
// structural check that runs on every write.

// TYPESCRIPT COMES FROM THE TREE IT GUARDS. This tool sits beside `editguard`
// in scoring/tools, which has no node_modules of its own; the compiler is a
// lo-blocks dependency. Resolving it by path keeps the two guards together
// rather than splitting them across repositories by an accident of packaging.
const { createRequire } = require('module');
const LO = process.env.LO_BLOCKS
  || '/home/pdeane/code/update/refactor_dry_run/lo-blocks';
const ts = createRequire(`${LO}/package.json`)('typescript');

/** Every exported name in a source text. */
function exportedNames(src, fileName = 'x.ts') {
  const sf = ts.createSourceFile(fileName, src, ts.ScriptTarget.Latest, true);
  const out = new Set();
  const isExported = (node) =>
    (ts.getCombinedModifierFlags(node) & ts.ModifierFlags.Export) !== 0;
  sf.forEachChild((node) => {
    if ((ts.isFunctionDeclaration(node) || ts.isClassDeclaration(node)
         || ts.isInterfaceDeclaration(node) || ts.isTypeAliasDeclaration(node)
         || ts.isEnumDeclaration(node)) && node.name && isExported(node)) {
      out.add(node.name.text);
    } else if (ts.isVariableStatement(node) && isExported(node)) {
      for (const d of node.declarationList.declarations) {
        if (ts.isIdentifier(d.name)) out.add(d.name.text);
      }
    }
  });
  return out;
}

/** Keys of every top-level exported object literal, as `TABLE['key']`. */
function registryKeys(src, fileName = 'x.ts') {
  const sf = ts.createSourceFile(fileName, src, ts.ScriptTarget.Latest, true);
  const out = new Set();
  sf.forEachChild((node) => {
    if (!ts.isVariableStatement(node)) return;
    for (const d of node.declarationList.declarations) {
      if (!ts.isIdentifier(d.name) || !d.initializer) continue;
      let init = d.initializer;
      while (ts.isAsExpression(init) || ts.isSatisfiesExpression(init)) init = init.expression;
      if (!ts.isObjectLiteralExpression(init)) continue;
      for (const prop of init.properties) {
        const n = prop.name;
        if (!n) continue;
        const key = ts.isIdentifier(n) ? n.text
          : ts.isStringLiteral(n) ? n.text : null;
        if (key) out.add(`${d.name.text}['${key}']`);
      }
    }
  });
  return out;
}

/** Does it parse? `createSourceFile` is lenient, so ask for real diagnostics. */
function parseErrors(src, fileName = 'x.ts') {
  const sf = ts.createSourceFile(fileName, src, ts.ScriptTarget.Latest, true);
  // `parseDiagnostics` is internal but is the only way to see syntax errors
  // without building a Program, which needs the whole dependency graph.
  const diags = sf.parseDiagnostics || [];
  return diags.map(d =>
    `${ts.flattenDiagnosticMessageText(d.messageText, ' ')} at position ${d.start}`);
}

/**
 * Refuse a write that silently loses something.
 *
 * `dropping` declares an intended loss, exactly as editguard's does: a bare
 * exported name, or `TABLE['key']`.
 */
function check(before, after, dropping = [], fileName = 'x.ts') {
  const problems = [];
  const errs = parseErrors(after, fileName);
  if (errs.length) {
    return [`${fileName} would not PARSE after this edit: ${errs[0]}. ` +
            `A broken file is the one loss that hides nothing -- but it is ` +
            `still better refused than written.`];
  }
  const declared = new Set(dropping);
  const lostNames = [...exportedNames(before, fileName)]
    .filter(n => !exportedNames(after, fileName).has(n) && !declared.has(n));
  if (lostNames.length) {
    problems.push(
      `${fileName}: ${lostNames.length} exported name(s) would vanish and were ` +
      `not declared -- ${lostNames.join(', ')}. If the removal is intended, ` +
      `pass them in dropping=; if not, the edit took more than it was aimed at`);
  }
  const afterKeys = registryKeys(after, fileName);
  const lostKeys = [...registryKeys(before, fileName)]
    .filter(k => !afterKeys.has(k) && !declared.has(k));
  if (lostKeys.length) {
    problems.push(
      `${fileName}: ${lostKeys.length} registry entr(ies) would vanish and were ` +
      `not declared -- ${lostKeys.join(', ')}. These are the tables this package ` +
      `dispatches on, so a lost key is a rule that silently stops being offered`);
  }
  const stillThere = [...declared].filter(d =>
    exportedNames(after, fileName).has(d) || afterKeys.has(d));
  if (stillThere.length) {
    problems.push(
      `${fileName}: declared dropping ${stillThere.join(', ')}, but they are ` +
      `STILL PRESENT afterwards -- the edit did not land where it was aimed`);
  }
  return problems;
}

module.exports = { check, exportedNames, registryKeys, parseErrors };

if (require.main === module) {
  const [, , beforePath, afterPath, ...dropping] = process.argv;
  const fs = require('fs');
  const problems = check(
    fs.readFileSync(beforePath, 'utf8'),
    fs.readFileSync(afterPath, 'utf8'),
    dropping, require('path').basename(beforePath));
  for (const p of problems) console.log(p);
  process.exit(problems.length ? 1 : 0);
}
