import React, { useState, useEffect } from 'react'
import { Edit2, Trash2, Plus, Check, X, Save } from 'lucide-react'

export default function EditReportTable({ attributes, onUpdate, onAdd, onDelete, saving }) {
  const [editingCell, setEditingCell] = useState(null)
  const [editingValue, setEditingValue] = useState('')
  const [editBuffer, setEditBuffer] = useState({})
  const [showAddRow, setShowAddRow] = useState(false)
  const [newAttribute, setNewAttribute] = useState({
    name: '',
    value: '',
    range: '',
    unit: '',
    remark: ''
  })

  // Convert attributes object to array for easier manipulation
  const getAttributesArray = () => {
    if (!attributes) return []
    
    return Object.entries(attributes).map(([key, attr]) => ({
      key,
      name: attr.name || key,
      value: attr.value || '',
      range: attr.range || '',
      unit: attr.unit || '',
      remark: attr.remark || ''
    }))
  }

  const attributesArray = getAttributesArray()

  const startEditing = (key, field, currentValue) => {
    setEditingCell({ key, field })
    setEditingValue(currentValue)
    setEditBuffer({ ...editBuffer, [`${key}-${field}`]: currentValue })
  }

  const cancelEditing = () => {
    setEditingCell(null)
    setEditingValue('')
  }

  const saveEdit = async () => {
    if (!editingCell) return

    const { key, field } = editingCell
    const updates = { [field]: editingValue }
    
    const result = await onUpdate(attributesArray.find(a => a.key === key).name, updates)
    
    if (result.success) {
      // Clear edit buffer for this field
      const newBuffer = { ...editBuffer }
      delete newBuffer[`${key}-${field}`]
      setEditBuffer(newBuffer)
      setEditingCell(null)
      setEditingValue('')
    } else {
      alert(`Failed to save: ${result.error}`)
    }
  }

  const handleDelete = async (key) => {
    const attribute = attributesArray.find(a => a.key === key)
    if (!attribute) return
    
    const result = await onDelete(attribute.name)
    
    if (!result.success) {
      alert(`Failed to delete: ${result.error}`)
    }
  }

  const handleAddAttribute = async () => {
    // Validate required fields
    if (!newAttribute.name.trim() || !newAttribute.value.trim()) {
      alert('Name and Value are required')
      return
    }

    const result = await onAdd({
      name: newAttribute.name.trim(),
      value: newAttribute.value.trim(),
      range: newAttribute.range.trim() || null,
      unit: newAttribute.unit.trim() || null,
      remark: newAttribute.remark.trim() || null
    })

    if (result.success) {
      // Reset form
      setNewAttribute({
        name: '',
        value: '',
        range: '',
        unit: '',
        remark: ''
      })
      setShowAddRow(false)
    } else {
      alert(`Failed to add: ${result.error}`)
    }
  }

  const getBufferedValue = (key, field, originalValue) => {
    return editBuffer[`${key}-${field}`] !== undefined 
      ? editBuffer[`${key}-${field}`] 
      : originalValue
  }

  const getFieldValueDisplay = (value) => {
    return value === null || value === undefined ? '' : String(value)
  }

  const getStatusColor = (attribute) => {
    if (!attribute.remark) return 'inherit'
    
    const remark = attribute.remark.toLowerCase()
    if (remark.includes('low') || remark.includes('decreased')) return '#dc2626'
    if (remark.includes('high') || remark.includes('elevated')) return '#dc2626'
    if (remark.includes('normal') || remark.includes('within')) return '#16a34a'
    return '#f59e0b'
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0 }}>Medical Test Results</h3>
        <button 
          className="button" 
          onClick={() => setShowAddRow(!showAddRow)}
          style={{ fontSize: '14px' }}
        >
          <Plus size={16} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
          Add New Test
        </button>
      </div>

      {saving && (
        <div style={{ backgroundColor: '#fef3c7', padding: '8px 12px', borderRadius: '4px', marginBottom: '12px', fontSize: '14px' }}>
          <span>⏳ Saving changes...</span>
        </div>
      )}

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
              <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>Test Name</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>Value</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>Range</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>Unit</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>Remark</th>
              <th style={{ padding: '12px 8px', textAlign: 'center', fontWeight: '600', color: '#374151' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {attributesArray.map((attribute) => (
              <tr key={attribute.key} style={{ borderBottom: '1px solid #e5e7eb', backgroundColor: 'white' }}>
                <td style={{ padding: '12px 8px', fontWeight: '500', color: getStatusColor(attribute) }}>
                  {editingCell?.key === attribute.key && editingCell?.field === 'name' ? (
                    <input
                      type="text"
                      value={editingValue}
                      onChange={(e) => setEditingValue(e.target.value)}
                      onBlur={() => saveEdit()}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveEdit()
                        if (e.key === 'Escape') cancelEditing()
                      }}
                      style={{ width: '100%', padding: '4px', border: '1px solid #3b82f6', borderRadius: '4px' }}
                      autoFocus
                    />
                  ) : (
                    <div 
                      onClick={() => startEditing(attribute.key, 'name', attribute.name)}
                      style={{ cursor: 'pointer', padding: '4px', borderRadius: '4px' }}
                      title="Click to edit"
                    >
                      {attribute.name}
                    </div>
                  )}
                </td>
                
                <td style={{ padding: '12px 8px' }}>
                  {editingCell?.key === attribute.key && editingCell?.field === 'value' ? (
                    <input
                      type="text"
                      value={editingValue}
                      onChange={(e) => setEditingValue(e.target.value)}
                      onBlur={() => saveEdit()}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveEdit()
                        if (e.key === 'Escape') cancelEditing()
                      }}
                      style={{ width: '100%', padding: '4px', border: '1px solid #3b82f6', borderRadius: '4px' }}
                      autoFocus
                    />
                  ) : (
                    <div 
                      onClick={() => startEditing(attribute.key, 'value', attribute.value)}
                      style={{ cursor: 'pointer', padding: '4px', borderRadius: '4px' }}
                      title="Click to edit"
                    >
                      {attribute.value}
                    </div>
                  )}
                </td>

                <td style={{ padding: '12px 8px' }}>
                  {editingCell?.key === attribute.key && editingCell?.field === 'range' ? (
                    <input
                      type="text"
                      value={editingValue}
                      onChange={(e) => setEditingValue(e.target.value)}
                      onBlur={() => saveEdit()}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveEdit()
                        if (e.key === 'Escape') cancelEditing()
                      }}
                      style={{ width: '100%', padding: '4px', border: '1px solid #3b82f6', borderRadius: '4px' }}
                      autoFocus
                    />
                  ) : (
                    <div 
                      onClick={() => startEditing(attribute.key, 'range', attribute.range)}
                      style={{ cursor: 'pointer', padding: '4px', borderRadius: '4px' }}
                      title="Click to edit"
                    >
                      {getFieldValueDisplay(attribute.range)}
                    </div>
                  )}
                </td>

                <td style={{ padding: '12px 8px' }}>
                  {editingCell?.key === attribute.key && editingCell?.field === 'unit' ? (
                    <input
                      type="text"
                      value={editingValue}
                      onChange={(e) => setEditingValue(e.target.value)}
                      onBlur={() => saveEdit()}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveEdit()
                        if (e.key === 'Escape') cancelEditing()
                      }}
                      style={{ width: '100%', padding: '4px', border: '1px solid #3b82f6', borderRadius: '4px' }}
                      autoFocus
                    />
                  ) : (
                    <div 
                      onClick={() => startEditing(attribute.key, 'unit', attribute.unit)}
                      style={{ cursor: 'pointer', padding: '4px', borderRadius: '4px' }}
                      title="Click to edit"
                    >
                      {getFieldValueDisplay(attribute.unit)}
                    </div>
                  )}
                </td>

                <td style={{ padding: '12px 8px' }}>
                  {editingCell?.key === attribute.key && editingCell?.field === 'remark' ? (
                    <input
                      type="text"
                      value={editingValue}
                      onChange={(e) => setEditingValue(e.target.value)}
                      onBlur={() => saveEdit()}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveEdit()
                        if (e.key === 'Escape') cancelEditing()
                      }}
                      style={{ width: '100%', padding: '4px', border: '1px solid #3b82f6', borderRadius: '4px' }}
                      autoFocus
                    />
                  ) : (
                    <div 
                      onClick={() => startEditing(attribute.key, 'remark', attribute.remark)}
                      style={{ cursor: 'pointer', padding: '4px', borderRadius: '4px' }}
                      title="Click to edit"
                    >
                      {getFieldValueDisplay(attribute.remark)}
                    </div>
                  )}
                </td>

                <td style={{ padding: '12px 8px', textAlign: 'center' }}>
                  <button
                    onClick={() => handleDelete(attribute.key)}
                    style={{ 
                      backgroundColor: '#fee2e2', 
                      color: '#dc2626', 
                      border: 'none', 
                      padding: '4px 8px', 
                      borderRadius: '4px', 
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                    title="Delete test"
                  >
                    <Trash2 size={14} style={{ verticalAlign: 'middle' }} />
                  </button>
                </td>
              </tr>
            ))}

            {/* Add new row */}
            {showAddRow && (
              <tr style={{ backgroundColor: '#f9fafb' }}>
                <td style={{ padding: '12px 8px' }}>
                  <input
                    type="text"
                    placeholder="Test name"
                    value={newAttribute.name}
                    onChange={(e) => setNewAttribute({...newAttribute, name: e.target.value})}
                    style={{ width: '100%', padding: '4px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                  />
                </td>
                <td style={{ padding: '12px 8px' }}>
                  <input
                    type="text"
                    placeholder="Value"
                    value={newAttribute.value}
                    onChange={(e) => setNewAttribute({...newAttribute, value: e.target.value})}
                    style={{ width: '100%', padding: '4px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                  />
                </td>
                <td style={{ padding: '12px 8px' }}>
                  <input
                    type="text"
                    placeholder="Range (optional)"
                    value={newAttribute.range}
                    onChange={(e) => setNewAttribute({...newAttribute, range: e.target.value})}
                    style={{ width: '100%', padding: '4px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                  />
                </td>
                <td style={{ padding: '12px 8px' }}>
                  <input
                    type="text"
                    placeholder="Unit (optional)"
                    value={newAttribute.unit}
                    onChange={(e) => setNewAttribute({...newAttribute, unit: e.target.value})}
                    style={{ width: '100%', padding: '4px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                  />
                </td>
                <td style={{ padding: '12px 8px' }}>
                  <input
                    type="text"
                    placeholder="Remark (optional)"
                    value={newAttribute.remark}
                    onChange={(e) => setNewAttribute({...newAttribute, remark: e.target.value})}
                    style={{ width: '100%', padding: '4px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                  />
                </td>
                <td style={{ padding: '12px 8px', textAlign: 'center' }}>
                  <button
                    onClick={handleAddAttribute}
                    disabled={saving}
                    style={{ 
                      backgroundColor: '#dcfce7', 
                      color: '#16a34a', 
                      border: 'none', 
                      padding: '4px 8px', 
                      borderRadius: '4px', 
                      cursor: 'pointer',
                      fontSize: '12px',
                      marginRight: '4px'
                    }}
                    title="Save new test"
                  >
                    <Check size={14} style={{ verticalAlign: 'middle' }} />
                  </button>
                  <button
                    onClick={() => setShowAddRow(false)}
                    style={{ 
                      backgroundColor: '#fee2e2', 
                      color: '#dc2626', 
                      border: 'none', 
                      padding: '4px 8px', 
                      borderRadius: '4px', 
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                    title="Cancel"
                  >
                    <X size={14} style={{ verticalAlign: 'middle' }} />
                  </button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {attributesArray.length === 0 && !showAddRow && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
          <p>No test results available.</p>
          <button 
            className="button" 
            onClick={() => setShowAddRow(true)}
            style={{ fontSize: '14px' }}
          >
            <Plus size={16} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
            Add First Test Result
          </button>
        </div>
      )}

      <div style={{ marginTop: '16px', fontSize: '12px', color: '#6b7280' }}>
        💡 Click any cell to edit • Color coding: <span style={{ color: '#16a34a' }}>Normal</span> • <span style={{ color: '#dc2626' }}>Abnormal</span> • <span style={{ color: '#f59e0b' }}>Borderline</span>
      </div>
    </div>
  )
}