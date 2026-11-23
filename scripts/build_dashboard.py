#!/usr/bin/env python3
"""CSV -> SQLite -> analysis.sql -> styled Excel tables and editable charts."""
import csv,json,sqlite3
from pathlib import Path
import xlsxwriter
ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'
INK='#251F21'; TEAL='#4C8877'; PALE='#E7F0EC'; SAND='#F4EFEC'; GREY='#8D9094'
def run_queries():
 c=sqlite3.connect(':memory:')
 rows=list(csv.DictReader(open(DATA/'matches_2015_2026.csv')))
 c.execute('CREATE TABLE matches(season TEXT, round TEXT, date TEXT, home_team TEXT, away_team TEXT, home_goals INTEGER, away_goals INTEGER, result TEXT, source TEXT)')
 c.executemany('INSERT INTO matches VALUES(?,?,?,?,?,?,?,?,?)',[tuple(r.values()) for r in rows])
 out=[]
 for q in (ROOT/'scripts/analysis.sql').read_text().split(';'):
  q='\n'.join(l for l in q.splitlines() if not l.strip().startswith('--')).strip()
  if q:
   cur=c.execute(q);out.append(([d[0] for d in cur.description],cur.fetchall()))
 return rows,out

def main():
 rows,res=run_queries();home,derby,ds,pyr,wins,goals,table=res
 n=len(rows);hp=100*sum(r['result']=='Home win' for r in rows)/n;ap=100*sum(r['result']=='Away win' for r in rows)/n
 modern=[r for r in pyr[1] if r[0]>='2018/19']
 aw=sum((r[2]=='Al Ahly' and r[3]>r[4]) or (r[5]=='Al Ahly' and r[4]>r[3]) for r in modern)
 pw=sum((r[2]=='Pyramids FC' and r[3]>r[4]) or (r[5]=='Pyramids FC' and r[4]>r[3]) for r in modern)
 summ={'matches':n,'seasons':len(home[1]),'home_pct':round(hp,1),'away_pct':round(ap,1),'derby':ds[1][0],'pyramids_modern':[aw,len(modern)-aw-pw,pw],'club_wins':wins[1],'table':table[1],'goals':goals[1]}
 (ROOT/'docs'/'findings.json').write_text(json.dumps(summ,indent=2))
 wb=xlsxwriter.Workbook(ROOT/'Egyptian_Premier_League_Analytics.xlsx')
 wb.formats[0].set_font_name('Calibri');wb.formats[0].set_font_size(11);wb.formats[0].set_font_color(INK)
 fmt=lambda **kw:wb.add_format(kw)
 title=fmt(bold=True,font_size=25,font_color=INK,bg_color=SAND,valign='vcenter')
 sub=fmt(font_size=11,font_color='#585254',bg_color=SAND,valign='vcenter')
 lbl=fmt(bold=True,font_size=10,font_color=TEAL,bg_color='#FFFFFF',valign='vcenter')
 val=fmt(bold=True,font_size=27,font_color=INK,bg_color='#FFFFFF',valign='vcenter')
 cap=fmt(font_size=10,font_color='#585254',bg_color='#FFFFFF',valign='vcenter')
 head=fmt(bold=True,font_size=14,font_color=INK,bg_color=SAND,valign='vcenter')
 note=fmt(font_size=10,font_color='#585254',bg_color=SAND,text_wrap=True,valign='vcenter')
 link=fmt(font_color=TEAL,bold=True,font_size=10,bg_color=SAND,underline=True)
 dash=wb.add_worksheet('Dashboard');dash.hide_gridlines(2);dash.set_zoom(85)
 dash.set_column('A:A',2);dash.set_column('B:Q',10);dash.set_column('R:R',2)
 for r in range(65):dash.set_row(r,22);dash.write_blank(r,0,None,fmt(bg_color=SAND))
 bg=fmt(bg_color=SAND)
 for r in range(65):
  for c in range(18):dash.write_blank(r,c,None,bg)
 dash.merge_range('B2:Q3','Egyptian Premier League',title)
 dash.merge_range('B4:Q4',f'2015/16 - 2026/27  |  {n:,} match records  |  12 seasons  |  Results through 31 Oct 2026',sub)
 d=ds[1][0];leader=table[1][0]
 cards=[('CAIRO DERBY',f'{d[0]} - {d[1]} - {d[2]}',f'Al Ahly wins / draws / Zamalek wins | {sum(d[:3])} records'),('AHLY vs PYRAMIDS',f'{aw} - {len(modern)-aw-pw} - {pw}','Ahly wins / draws / Pyramids wins | since 2018/19'),('2026/27 LEADER',f'{leader[8]} points',f'{leader[0]} | {leader[2]} wins from {leader[1]} games'),('HOME WIN RATE',f'{hp:.1f}%',f'Away wins {ap:.1f}% | gap {hp-ap:.1f} percentage points')]
 for i,(a,b,c) in enumerate(cards):
  col=1+i*4
  dash.merge_range(6,col,6,col+3,a,lbl);dash.merge_range(7,col,8,col+3,b,val);dash.merge_range(9,col,10,col+3,c,fmt(font_size=10,font_color='#585254',bg_color='white',text_wrap=True,valign='vcenter'))
 def detail(name,header,data):
  ws=wb.add_worksheet(name);ws.hide_gridlines(2);ws.freeze_panes(4,0);ws.set_zoom(90)
  ws.merge_range(0,0,0,max(5,len(header)-1),name,fmt(font_size=20,bold=True,font_color=INK))
  ws.write_url(1,0,"internal:'Dashboard'!B2",link,'Back to dashboard')
  ws.set_column(0,len(header)-1,16)
  for i,h in enumerate(header):
   if 'team' in h or h in ['player','club']:ws.set_column(i,i,30)
  ws.add_table(3,0,3+len(data),len(header)-1,{'data':data,'columns':[{'header':h} for h in header],'style':'Table Style Medium 2'})
  ws.set_landscape();ws.fit_to_pages(1,0);ws.repeat_rows(0,3)
  ws.print_area(0,0,3+len(data),len(header)-1)
  return ws
 detail('Home Advantage',*home);detail('Cairo Derby',*derby);detail('Ahly vs Pyramids',*pyr);detail('Table 2026-27',*table);detail('Goals by Season',*goals);detail('Club Wins',*wins)
 scorers=list(csv.reader(open(DATA/'top_scorers_by_season.csv')));detail('Top Scorers',scorers[0],[[*r[:3],int(r[3])] for r in scorers[1:]])
 detail('Match Data',list(rows[0]),[[r[k] if k not in ['home_goals','away_goals'] else int(r[k]) for k in rows[0]] for r in rows])
 quality=[['Range','2015/16 to 2026/27; no pre-2015 records in analysis.'],['Freshness','Results through 31 Oct 2026. Static snapshot, not a live workbook.'],['Coverage','2019/20 has 298 records. Season completeness is not guaranteed.'],['Result meaning','Source scores may include awarded outcomes, not only played games.'],['Home advantage','Home/away are fixture labels, not proof of venue or crowd effect.'],['Current table','3 points per win, 1 per draw; sorted points, goal difference, goals for. No deductions or special tie-breaks.'],['Pyramids','Pre-2018 Alassiouty Sport is normalized to Pyramids FC in raw detail; KPI starts 2018/19.'],['Scorers','Season-award table from Wikipedia; 2026/27 award not yet available.'],['Source 2015-18','https://github.com/abdelmalek13/Egyptian-League-Analysis'],['Source 2018-26','https://www.sofascore.com/tournament/football/egypt/premier-league/808'],['Scorer source','https://en.wikipedia.org/wiki/Egyptian_Premier_League']]
 q=detail('Read Me',['Topic','Details'],quality);q.set_column(0,0,23);q.set_column(1,1,115)
 def chart(typ,title,anchor,width=570,height=320):
  ch=wb.add_chart({'type':typ});ch.set_title({'name':title,'name_font':{'size':13,'bold':True,'color':INK}});ch.set_chartarea({'border':{'none':True},'fill':{'color':'white'}});ch.set_plotarea({'border':{'none':True}});ch.set_size({'width':width,'height':height});ch.set_legend({'position':'bottom','font':{'size':10}});ch.set_x_axis({'num_font':{'size':9},'line':{'none':True}});ch.set_y_axis({'num_font':{'size':9},'major_gridlines':{'visible':True,'line':{'color':'#EAE9EA'}},'line':{'none':True}});dash.insert_chart(anchor,ch,{'x_offset':0,'y_offset':0});return ch
 ch=chart('column','Home advantage by season (%)','B13')
 for name,col,color in [('Home wins',5,TEAL),('Away wins',6,'#BABDBF')]:ch.add_series({'name':name,'categories':['Home Advantage',4,0,15,0],'values':['Home Advantage',4,col,15,col],'fill':{'color':color},'border':{'none':True}})
 ch.set_y_axis({'min':0,'max':60,'major_gridlines':{'visible':True,'line':{'color':'#EAE9EA'}}});ch.set_x_axis({'num_font':{'size':9,'rotation':-45}})
 ch=chart('bar','Most league wins | selected range','J13');ch.add_series({'name':'Wins','categories':['Club Wins',4,0,11,0],'values':['Club Wins',4,1,11,1],'fill':{'color':TEAL},'border':{'none':True},'data_labels':{'value':True,'position':'outside_end','font':{'size':10}}});ch.set_legend({'none':True});ch.set_y_axis({'reverse':True,'num_font':{'size':10},'major_gridlines':{'visible':False}})
 ch=chart('line','Goals per game | compare season intensity','B29',570,265);ch.add_series({'name':'Goals / game','categories':['Goals by Season',4,0,15,0],'values':['Goals by Season',4,2,15,2],'line':{'color':TEAL,'width':2.5},'marker':{'type':'circle','size':5,'border':{'color':TEAL},'fill':{'color':'white'}}});ch.set_legend({'none':True});ch.set_y_axis({'min':0,'max':3,'major_gridlines':{'visible':True,'line':{'color':'#EAE9EA'}}});ch.set_x_axis({'num_font':{'size':9,'rotation':-45}})
 dash.merge_range('J29:Q30','2026/27 | leading teams',head)
 th=fmt(bold=True,font_color=TEAL,bg_color=PALE);cell=fmt(bg_color='white',font_size=11);pts=fmt(bg_color=PALE,bold=True,font_color=TEAL,align='center')
 for a,b,txt in [('J31:M31','', 'Club'),('N31:N31','','P'),('O31:O31','','GD'),('P31:Q31','','Pts')]:
  if a.split(':')[0]==a.split(':')[1]:dash.write(a.split(':')[0],txt,th)
  else:dash.merge_range(a,txt,th)
 for i,r in enumerate(table[1][:8],32):
  dash.merge_range(f'J{i}:M{i}',f'{i-31:02d}  '+{'Arab Contractors (Al Mokawloon)':'Arab Contractors','Al Ittihad Alexandria':'Al Ittihad Alex.','National Bank of Egypt':'National Bank'}.get(r[0],r[0]),cell);dash.write(f'N{i}',r[1],cell);dash.write(f'O{i}',r[7],cell);dash.merge_range(f'P{i}:Q{i}',r[8],pts)
 dash.merge_range('J40:Q41','Calculated standings, not an official table. Full detail in Table 2026-27.',note)
 dash.merge_range('B44:Q44','Explore the detail',head)
 for i,(label,sheet) in enumerate([('Home advantage','Home Advantage'),('Cairo Derby','Cairo Derby'),('Ahly vs Pyramids','Ahly vs Pyramids'),('Current table','Table 2026-27'),('Goals by season','Goals by Season'),('Club wins','Club Wins'),('Top scorers','Top Scorers'),('Data + method','Read Me')]):
  row=45+(i//4)*2;col=1+(i%4)*4;dash.merge_range(row,col,row,col+3,'',link);dash.write_url(row,col,f"internal:'{sheet}'!A1",link,label+' >')
 dash.merge_range('B50:Q51','Reading the numbers: these are source-record results, including possible awarded scores. The 2019/20 snapshot has 298 records; completeness is not guaranteed. Home advantage is descriptive, not a causal claim.',note)
 dash.merge_range('B53:Q54','Sources: public GitHub match dataset (2015/16-2017/18), Sofascore API (2018/19-2026/27), Wikipedia season top scorers. Rebuild with Python + SQLite + XlsxWriter. See Read Me for source links and methods.',note)
 dash.set_portrait();dash.set_paper(8);dash.fit_to_pages(1,1);dash.set_margins(.2,.2,.2,.2);dash.print_area('A1:R56');dash.activate();dash.set_first_sheet();wb.close();print(json.dumps(summ,indent=2))
if __name__=='__main__':main()
