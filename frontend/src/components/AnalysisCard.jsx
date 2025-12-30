import React from 'react'
import { CheckCircle, Plus } from 'lucide-react'

export default function AnalysisCard({analysis, compact=false, onAddFavorite, favoriteMarkers = []}){
  if(!analysis) return null
  
  // Ensure analysis has required properties with fallbacks
  const {
    interpretation = "No interpretation available",
    lifestyle_changes = [],
    nutritional_changes = [],
    symptom_probable_cause = null,
    next_steps = [],
    concern_options = []
  } = analysis

  return (
    <div className="card analysis-card">
      <h3 style={{marginTop:0}}>{compact ? "Analysis Summary" : "Analysis"}</h3>

      <div className="analysis-interpretation">
        <strong>Interpretation</strong>
        <p className="small-muted">{interpretation}</p>
      </div>

      <div className="analysis-sections">
        {lifestyle_changes && lifestyle_changes.length > 0 && (
          <div className="analysis-section">
            <h4>Lifestyle changes</h4>
            <ul className="analysis-list">
              {lifestyle_changes.map((c,i)=> (
                <li key={i}><CheckCircle size={16} style={{verticalAlign:'middle', marginRight:8, color:'#06b6d4'}}/>{c}</li>
              ))}
            </ul>
          </div>
        )}

        {nutritional_changes && nutritional_changes.length > 0 && (
          <div className="analysis-section">
            <h4>Nutritional changes</h4>
            <ul className="analysis-list">
              {nutritional_changes.map((c,i)=>(<li key={i}>{c}</li>))}
            </ul>
          </div>
        )}

        {symptom_probable_cause && (
          <div className="analysis-section">
            <h4>Probable cause</h4>
            <p>{symptom_probable_cause}</p>
          </div>
        )}

        {next_steps && next_steps.length > 0 && (
          <div className="analysis-section">
            <h4>Next steps</h4>
            <ol className="analysis-nextsteps">
              {next_steps.map((s,i)=>(<li key={i}>{s}</li>))}
            </ol>
          </div>
        )}

         {concern_options && concern_options.length > 0 && (
           <div className="analysis-section">
             <h4>Concern options</h4>
             <div className="concern-chips">
               {concern_options.map((c,i)=> {
                 const isFavorite = favoriteMarkers.some(fav => fav.toLowerCase() === c.toLowerCase())
                 return (
                   <span 
                     key={i} 
                     className={`chip ${isFavorite ? 'chip-favorite' : 'chip-clickable'}`}
                     onClick={() => !isFavorite && onAddFavorite && onAddFavorite(c)}
                     title={isFavorite ? "Already in favorites" : "Click to add to favorites"}
                     style={{
                       cursor: isFavorite ? 'default' : 'pointer',
                       backgroundColor: isFavorite ? '#16a34a' : undefined,
                       color: isFavorite ? 'white' : undefined,
                       display: 'inline-flex',
                       alignItems: 'center',
                       gap: '4px'
                     }}
                   >
                     {isFavorite ? '✓' : <Plus size={12} />}
                     {c}
                   </span>
                 )
               })}
             </div>
           </div>
         )}
      </div>

      {!compact && (
        <p style={{fontSize:12, color:'#6b7280', marginTop:12}}>
          AI-generated medical analysis. Consult healthcare professionals for medical advice.
        </p>
      )}
    </div>
  )
}
