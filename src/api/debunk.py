import html as _html
import markdown

_FLICC_ICON_BASE = "https://commons.wikimedia.org/wiki/Special:Redirect/file"

FLICC_ICON_MAP = {
    "ad hominem": f"{_FLICC_ICON_BASE}/Ad_Hominem_Fallacy_Icon_Black.svg",
    "anecdote": f"{_FLICC_ICON_BASE}/Anecdote_Fallacy_Icon_Black.svg",
    "cherry picking": f"{_FLICC_ICON_BASE}/Cherry_Picking_Fallacy_Icon_Black.svg",
    "conspiracy theory": f"{_FLICC_ICON_BASE}/Conspiracy_Theories_Fallacy_Icon_Black.svg",
    "fake experts": f"{_FLICC_ICON_BASE}/Fake_Experts_Fallacy_Icon_Black.svg",
    "false choice": f"{_FLICC_ICON_BASE}/False_Choice_Fallacy_Icon_Black.svg",
    "impossible expectations": f"{_FLICC_ICON_BASE}/Impossible_Expectations_Fallacy_Icon_Black.svg",
    "misrepresentation": f"{_FLICC_ICON_BASE}/Misrepresentation_Fallacy_Icon_Black.svg",
    "oversimplification": f"{_FLICC_ICON_BASE}/Oversimplification_Fallacy_Icon_Black.svg",
    "slothful induction": f"{_FLICC_ICON_BASE}/Slothful_Induction_Fallacy_Icon_Black.svg",
    "single cause": f"{_FLICC_ICON_BASE}/Single_Cause_Fallacy_Icon_Black.svg",
    "false equivalence": f"{_FLICC_ICON_BASE}/False_Analogy_Fallacy_Icon_Black.svg",
}

_FLICC_FALLBACK_ICON = f"{_FLICC_ICON_BASE}/Logical_Fallacies_Fallacy_Icon_Black.svg"

_CSS = """                                            
  <style>                                                                                                                                                
    .ds-wrapper {                                       
      font-family: inherit;                                                                                                                              
      padding: 4px;
      margin-bottom: 20px;                                                                                                                               
    }                                                                                                                                                    
    .ds-section-title {
      font-size: 1rem;                                                                                                                                   
      font-weight: 600;                                 
      color: #374151;                                                                                                                                    
      margin: 0 0 12px 0;
      padding-bottom: 6px;                                                                                                                               
      border-bottom: 2px solid #e5e7eb;                                                                                                                  
    }
    .ds-stat-grid {                                                                                                                                      
      display: grid;                                    
      grid-template-columns: repeat(2, 1fr);                                                                                                             
      gap: 10px;
      margin-bottom: 12px;                                                                                                                               
    }                                                   
    .ds-stat-card {
      background: #f9fafb;                                                                                                                               
      border: 1px solid #e5e7eb;
      border-radius: 10px;                                                                                                                               
      padding: 14px 12px;                               
      text-align: center;                                                                                                                                
    }
    .ds-stat-card--warning { background: #fffbeb; border-color: #fcd34d; }                                                                               
    .ds-stat-card--ok      { background: #f0fdf4; border-color: #bbf7d0; }                                                                               
    .ds-stat-icon  { font-size: 1.3rem; margin-bottom: 4px; }                                                                                            
    .ds-stat-value { font-size: 1.4rem; font-weight: 700; color: #1f2937; margin-bottom: 2px; }                                                          
    .ds-stat-pct   { font-size: 0.9rem; font-weight: 500; color: #d97706; }                                                                              
    .ds-stat-label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #6b7280; }                           
    .ds-findings-block {                                                                                                                                 
      background: #eff6ff;                                                                                                                               
      border: 1px solid #bfdbfe;                                                                                                                         
      border-radius: 10px;                                                                                                                               
      padding: 14px;
      margin-bottom: 12px;                                                                                                                               
    }                                                   
    .ds-findings-label {
      font-size: 0.7rem;
      font-weight: 600;                                                                                                                                  
      text-transform: uppercase;
      letter-spacing: 0.05em;                                                                                                                            
      color: #3b82f6;                                   
      margin-bottom: 10px;
    }                                                                                                                                                    
    .ds-findings-row { margin-bottom: 10px; }
    .ds-findings-row:last-child { margin-bottom: 0; }                                                                                                    
    .ds-findings-sublabel {                                                                                                                              
      font-size: 0.72rem;
      font-weight: 600;                                                                                                                                  
      color: #1e40af;                                   
      display: block;                                                                                                                                    
      margin-bottom: 6px;
    }                                                                                                                                                    
    .ds-pills { display: flex; flex-wrap: wrap; gap: 6px; }
    .ds-pill {                                                                                                                                           
      display: inline-flex;
      align-items: center;                                                                                                                               
      gap: 5px;                                         
      padding: 4px 10px;                                                                                                                                 
      border-radius: 20px;                              
      font-size: 0.78rem;                                                                                                                                
      font-weight: 500;
    }                                                                                                                                                    
    .ds-pill--flicc { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
    .ds-pill--cards { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }                                                                  
    .ds-pill-icon   { width: 18px; height: 18px; object-fit: contain; }                                                                                  
    .ds-pill-code   { font-family: monospace; font-size: 0.68rem; background: #dcfce7; padding: 1px 4px; border-radius: 3px; }                           
    .ds-analysis-block {                                                                                                                                 
      background: #f9fafb;                                                                                                                               
      border: 1px solid #e5e7eb;                                                                                                                         
      border-radius: 10px;                                                                                                                               
      padding: 14px;
      margin-top: 12px;                                                                                                                                  
    }                                                   
    .ds-analysis-title {
      font-size: 0.7rem;
      font-weight: 600;                                                                                                                                  
      text-transform: uppercase;
      letter-spacing: 0.05em;                                                                                                                            
      color: #6b7280;                                   
      margin-bottom: 10px;
    }                                                                                                                                                    
    .ds-analysis-section { margin-bottom: 12px; }
    .ds-analysis-section:last-child { margin-bottom: 0; }                                                                                                
    .ds-analysis-sublabel { font-size: 0.72rem; font-weight: 600; color: #374151; display: block; margin-bottom: 4px; }
    .ds-analysis-text { font-size: 0.85rem; color: #374151; line-height: 1.6; margin: 0; }                                                               
    .ds-clean-block {                                                                                                                                    
      background: #f0fdf4;                                                                                                                               
      border: 1px solid #bbf7d0;                                                                                                                         
      border-radius: 10px;                              
      padding: 16px;                                                                                                                                     
      display: flex;
      align-items: center;                                                                                                                               
      gap: 10px;                                        
      margin-bottom: 12px;
    }
    .ds-clean-icon { font-size: 1.4rem; }                                                                                                                
    .ds-clean-text { font-size: 0.9rem; font-weight: 500; color: #166534; }
  </style>                                                                                                                                               
"""


def _analysis_block_html(summary, include_denial_tactics: bool) -> str:
    if summary is None:
        return ""
    sections = f"""
    <div class="ds-analysis-section">                                                                                                                
        <span class="ds-analysis-sublabel">Article Summary</span>
        <p class="ds-analysis-text">{_html.escape(summary.article_summary)}</p>                                                                        
    </div>"""
    if include_denial_tactics and summary.debunking_summary:
        sections += f"""                                                                                                                               
    <div class="ds-analysis-section">
        <span class="ds-analysis-sublabel">Denial Tactics</span>                                                                                       
        <p class="ds-analysis-text">{_html.escape(summary.debunking_summary)}</p>                                                                      
    </div>"""
    return f"""                                                                                                                                        
<div class="ds-analysis-block">                     
    <div class="ds-analysis-title">Analysis</div>                                                                                                      
    {sections}
</div>"""


def render_debunk_html(state: dict) -> str:
    chunks = state["chunks"]
    total = len(chunks)
    misinfo = [c for c in chunks if c.get("has_misinformation")]
    flagged = len(misinfo)
    pct = round(flagged / total * 100) if total else 0
    summary = state.get("_debunk_summary")

    # --- stat cards ---
    flag_class = "ds-stat-card--warning" if flagged else "ds-stat-card--ok"
    flag_icon = "⚠️ " if flagged else "✅"
    stat_grid = f"""
<div class="ds-stat-grid">                                                                                                                           
    <div class="ds-stat-card">                        
    <div class="ds-stat-icon">📄</div>                                                                                                               
    <div class="ds-stat-value">{total}</div>                                                                                                         
    <div class="ds-stat-label">Passages Analyzed</div>
    </div>                                                                                                                                             
    <div class="ds-stat-card {flag_class}">           
    <div class="ds-stat-icon">{flag_icon}</div>                                                                                                      
    <div class="ds-stat-value">{flagged} <span class="ds-stat-pct">({pct}%)</span></div>                                                             
    <div class="ds-stat-label">Flagged as Misinformation</div>                                                                                       
    </div>                                                                                                                                             
</div>"""

    if not flagged:
        # Clean article — show green block + article summary only
        body = f"""                                                                                                                                    
<div class="ds-clean-block">                        
    <span class="ds-clean-icon">✅</span>                                                                                                              
    <span class="ds-clean-text">No misinformation detected in this article.</span>
</div>                                                                                                                                               
{_analysis_block_html(summary, include_denial_tactics=False)}"""
    else:
        # Misinfo found — findings block + full analysis
        unique_fallacies = list(
            dict.fromkeys(c["fallacy"] for c in misinfo if c.get("fallacy"))
        )
        unique_cards = list(
            dict.fromkeys(
                (c["CARDS_code"], c["CARDS_category"])
                for c in misinfo
                if c.get("CARDS_code") and c.get("CARDS_category")
            )
        )

        flicc_pills = "".join(
            f"""<span class="ds-pill ds-pill--flicc">
            <img src="{FLICC_ICON_MAP.get(label.lower(), _FLICC_FALLBACK_ICON)}" class="ds-pill-icon" alt="" />                                      
            {_html.escape(label.title())}                                                                                                            
            </span>"""
            for label in unique_fallacies
        )
        cards_pills = "".join(
            f"""<span class="ds-pill ds-pill--cards">
            <span class="ds-pill-code">{_html.escape(code)}</span>                                                                                   
            {_html.escape(desc)}                                                                                                                     
            </span>"""
            for code, desc in unique_cards
        )

        body = f"""
<div class="ds-findings-block">
    <div class="ds-findings-label">Misinformation Found</div>
    <div class="ds-findings-row">                                                                                                                      
    <span class="ds-findings-sublabel">FLICC Techniques</span>
    <div class="ds-pills">{flicc_pills}</div>                                                                                                        
    </div>                                            
    <div class="ds-findings-row">                                                                                                                      
    <span class="ds-findings-sublabel">CARDS Categories</span>
    <div class="ds-pills">{cards_pills}</div>                                                                                                        
    </div>
</div>                                                                                                                                               
{_analysis_block_html(summary, include_denial_tactics=True)}"""

    # --- annotated text (existing logic, moved from main.py) ---
    detail = '<div class="text-container">'
    for chunk in chunks:
        text_html = markdown.markdown(chunk.get("text", ""))
        is_bad = chunk.get("has_misinformation", False)
        rebuttal = (
            markdown.markdown(chunk.get("rebuttal"))
            if isinstance(chunk.get("rebuttal"), str)
            else ""
        )
        if is_bad:
            detail += f"""
            <div class="misinfo-trigger" tabindex="0">
                {text_html}                                                                                                                            
                <div class="rebuttal-content">
                    <span class="rebuttal-label">⚠️  Rebuttal:</span>                                                                                   
                    {rebuttal}                        
                </div>                                                                                                                                 
            </div>"""
        else:
            detail += f'<div class="neutral-chunk">{text_html}</div>'
    detail += "</div>"

    return f"""{_CSS}
<div class="ds-wrapper">                                                                                                                               
<p class="ds-section-title">🔍 Claim Debunking Analysis</p>
{stat_grid}                                                                                                                                          
{body}
</div>                                                                                                                                                 
{detail}"""
