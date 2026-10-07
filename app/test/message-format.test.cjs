const test=require('node:test'),assert=require('node:assert/strict');
test('Agent output renders headings, lists, emphasis, tables and wrapped code safely',async()=>{
 const {renderMessage}=await import('../ui/message-format.mjs');
 const out=renderMessage('# Prepared\n\n- **Mesh:** 90 C3D8\n- Load: `750 N`\n\n```text\n/path/prepared.inp\n```\n\n| Check | Status |\n| --- | --- |\n| Solver | Passed |');
 assert.match(out,/<h3>Prepared<\/h3>/);assert.match(out,/<ul><li><strong>Mesh:<\/strong>/);assert.match(out,/<code>750 N<\/code>/);assert.match(out,/<pre><code>\/path\/prepared.inp/);assert.match(out,/<table>/);
 const malicious=renderMessage('<img src=x onerror=alert(1)>\n<script>alert(1)</script>\n\n[unsafe](javascript:alert(1))\n\n```\n</code><img src=x>\n```');
 assert.doesNotMatch(malicious,/<img|<script|href=|onclick=/);assert.match(malicious,/&lt;img/);assert.match(renderMessage('**working'),/\*\*working/);
});
