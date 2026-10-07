// Render the common agent Markdown subset. Raw HTML is always escaped.
const escape=text=>String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function inline(text){
 return text.split(/(`[^`\n]+`|\*\*[^*\n]+\*\*|__[^_\n]+__|\*[^*\n]+\*|\[[^\]\n]+\]\([^\)\n]+\))/g).map(part=>{
  if(/^`[^`]+`$/.test(part))return '<code>'+escape(part.slice(1,-1))+'</code>';
  if(/^(?:\*\*[^*\n]+\*\*|__[^_\n]+__)$/.test(part))return '<strong>'+escape(part.slice(2,-2))+'</strong>';
  if(/^\*[^*]+\*$/.test(part))return '<em>'+escape(part.slice(1,-1))+'</em>';
  const link=/^\[([^\]]+)\]\(([^)]+)\)$/.exec(part);
  if(link)return escape(link[1])+' <span class="chat-url">('+escape(link[2])+')</span>';
  return escape(part);
 }).join('');
}
export function renderMessage(text){
 const lines=String(text).replace(/\r\n/g,'\n').split('\n');let out='',i=0;
 const tableCells=line=>line.trim().replace(/^\||\|$/g,'').split('|').map(c=>inline(c.trim()));
 while(i<lines.length){
  const line=lines[i];
  if(!line.trim()){i++;continue;}
  if(/^\s*```/.test(line)){
   let content=[];i++;while(i<lines.length&&!/^\s*```/.test(lines[i]))content.push(lines[i++]);
   if(i<lines.length)i++;out+='<pre><code>'+escape(content.join('\n'))+'</code></pre>';continue;
  }
  const heading=/^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$/.exec(line);
  if(heading){out+='<h3>'+inline(heading[1])+'</h3>';i++;continue;}
  if(/^\s*(?:---+|\*\*\*+)\s*$/.test(line)){out+='<hr>';i++;continue;}
  if(line.includes('|')&&i+1<lines.length&&/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[i+1])){
   const headers=tableCells(line);i+=2;out+='<div class="chat-table"><table><thead><tr>'+headers.map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody>';
   while(i<lines.length&&lines[i].includes('|'))out+='<tr>'+tableCells(lines[i++]).map(c=>'<td>'+c+'</td>').join('')+'</tr>';
   out+='</tbody></table></div>';continue;
  }
  const list=/^\s*(?:([-+*])|(\d+)[.)])\s+(.+)$/.exec(line);
  if(list){const ordered=!!list[2],tag=ordered?'ol':'ul';out+='<'+tag+(ordered?' start="'+Number(list[2])+'"':'')+'>';
   while(i<lines.length){const item=/^\s*(?:([-+*])|(\d+)[.)])\s+(.+)$/.exec(lines[i]);if(!item||!!item[2]!==ordered)break;let body=item[3];i++;
    while(i<lines.length&&/^\s{2,}\S/.test(lines[i])&&!/^\s*([-+*]|\d+[.)])\s/.test(lines[i]))body+=' '+lines[i++].trim();
    out+='<li>'+inline(body)+'</li>';
   }out+='</'+tag+'>';continue;
  }
  if(/^>\s?/.test(line)){let body=[];while(i<lines.length&&/^>\s?/.test(lines[i]))body.push(lines[i++].replace(/^>\s?/,''));out+='<blockquote>'+inline(body.join(' '))+'</blockquote>';continue;}
  let paragraph=[line];i++;while(i<lines.length&&lines[i].trim()&&!/^\s*(#{1,6}\s|```|[-+*]\s|\d+[.)]\s|>\s)/.test(lines[i])&&!(lines[i].includes('|')&&i+1<lines.length&&lines[i+1].includes('---')))paragraph.push(lines[i++]);
  out+='<p>'+inline(paragraph.join('\n')).replace(/\n/g,'<br>')+'</p>';
 }return out;
}
