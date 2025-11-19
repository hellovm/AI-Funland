const t = {
  en: {
    qa_title: 'Q&A',
    models_title: 'Model Management',
    sys_title: 'System Panel',
    refreshModels: 'Refresh Models',
    send: 'Send',
    download: 'Download',
    quantize: 'Quantize',
    delete: 'Delete',
    quant_cfg_title: 'Quantization Config',
    bits_label: 'Precision (bits)',
    method_label: 'Algorithm',
    range_label: 'Range',
    dataset_label: 'Dataset',
    weight_dtype_label: 'Weight dtype',
    activation_dtype_label: 'Activation dtype',
    save_preset: 'Save Preset',
    load_preset: 'Load Preset',
    export_preset: 'Export Preset',
    import_preset: 'Import Preset'
  },
  zh: {
    qa_title: '问答',
    models_title: '模型管理',
    sys_title: '系统检测',
    refreshModels: '刷新模型',
    send: '发送',
    download: '下载',
    quantize: '量化',
    delete: '删除',
    quant_cfg_title: '量化参数配置',
    bits_label: '量化精度（位）',
    method_label: '量化算法',
    range_label: '量化范围',
    dataset_label: '校准数据集',
    weight_dtype_label: '权重数据类型',
    activation_dtype_label: '激活数据类型',
    save_preset: '保存预设',
    load_preset: '加载预设',
    export_preset: '导出预设',
    import_preset: '导入预设'
  }
}

let lang = 'en'
let toastTimer = null

function showToast(msg){
  const el = document.getElementById('toast')
  el.textContent = msg
  el.style.display = 'block'
  clearTimeout(toastTimer)
  toastTimer = setTimeout(()=>{ el.style.display='none' }, 4000)
}

function i18n() {
  const d = t[lang]
  document.getElementById('qa_title').textContent = d.qa_title
  document.getElementById('models_title').textContent = d.models_title
  document.getElementById('sys_title').textContent = d.sys_title
  document.getElementById('refreshModels').textContent = d.refreshModels
  document.getElementById('send').textContent = d.send
  document.getElementById('download').textContent = d.download
  document.getElementById('quantize').textContent = d.quantize
  document.getElementById('delete').textContent = d.delete
  document.getElementById('quant_cfg_title').textContent = d.quant_cfg_title
  document.getElementById('bits_label').textContent = d.bits_label
  document.getElementById('method_label').textContent = d.method_label
  document.getElementById('range_label').textContent = d.range_label
  document.getElementById('dataset_label').textContent = d.dataset_label
  document.getElementById('weight_dtype_label').textContent = d.weight_dtype_label
  document.getElementById('activation_dtype_label').textContent = d.activation_dtype_label
  document.getElementById('save_preset').textContent = d.save_preset
  document.getElementById('load_preset').textContent = d.load_preset
  document.getElementById('import_preset').textContent = d.import_preset
  document.getElementById('export_preset').textContent = d.export_preset
}

async function loadAccelerators() {
  try{
    const r = await fetch('/api/accelerators')
    const j = await r.json()
    const sel = document.getElementById('device')
    sel.innerHTML = ''
    j.devices.forEach(d => {
      const o = document.createElement('option')
      o.value = d
      o.textContent = d
      sel.appendChild(o)
    })
  }catch(e){ showToast('Load accelerators failed') }
}

async function loadModels() {
  try{
    const r = await fetch('/api/models')
    const j = await r.json()
    const sel = document.getElementById('model')
    sel.innerHTML = ''
    j.models.forEach(m => {
      const o = document.createElement('option')
      o.value = m.id
      o.textContent = m.id
      sel.appendChild(o)
    })
  }catch(e){ showToast('Load models failed') }
}

async function loadSys() {
  try{
    const r = await fetch('/api/hardware')
    const j = await r.json()
    document.getElementById('sysinfo').textContent = JSON.stringify(j, null, 2)
  }catch(e){ showToast('Load system info failed') }
}

async function sendChat() {
  const model_id = document.getElementById('model').value
  const prompt = document.getElementById('prompt').value
  const device = document.getElementById('device').value
  try{
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_id, prompt, device, max_new_tokens: 256 })
    })
    const j = await r.json()
    document.getElementById('output').textContent = j.text || j.error
  }catch(e){ showToast('Chat request failed') }
}

async function downloadModel() {
  const model_id = document.getElementById('model_id').value
  const r = await fetch('/api/models/download', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id })
  })
  const j = await r.json()
  if (j.task_id) trackDownload(j.task_id)
}

async function trackDownload(task_id) {
  const div = document.getElementById('downloads')
  const wrap = document.createElement('div')
  wrap.className = 'progress'
  const bar = document.createElement('div')
  bar.className = 'bar'
  const text = document.createElement('div')
  text.className = 'meta'
  const controls = document.createElement('div')
  controls.className = 'controls'
  const pauseBtn = document.createElement('button')
  pauseBtn.textContent = 'Pause'
  const resumeBtn = document.createElement('button')
  resumeBtn.textContent = 'Resume'
  controls.appendChild(pauseBtn)
  controls.appendChild(resumeBtn)
  wrap.appendChild(bar)
  wrap.appendChild(text)
  wrap.appendChild(controls)
  div.appendChild(wrap)
  const tick = async () => {
    let j
    try{
      const r = await fetch('/api/models/download/status/' + task_id)
      j = await r.json()
    }catch(e){ showToast('Download status failed'); setTimeout(tick, 1500); return }
    if (j.status === 'completed' || j.status === 'error') {
      text.textContent = j.status
      loadModels()
      return
    }
    const pct = j.progress || 0
    bar.style.width = pct + '%'
    const speed = j.speed_bps || 0
    const speedText = speed > 1024*1024 ? (speed/1024/1024).toFixed(2) + ' MB/s' : (speed/1024).toFixed(2) + ' KB/s'
    const eta = j.eta_seconds != null ? formatETA(j.eta_seconds) : '?'
    text.textContent = `Progress ${pct}% | Speed ${speedText} | ETA ${eta}`
    setTimeout(tick, 1000)
  }
  pauseBtn.onclick = async ()=>{ await fetch('/api/models/download/pause', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ task_id }) }) }
  resumeBtn.onclick = async ()=>{ await fetch('/api/models/download/resume', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ task_id }) }) }
  tick()
}

function formatETA(s){
  const h = Math.floor(s/3600)
  const m = Math.floor((s%3600)/60)
  const sec = Math.floor(s%60)
  if(h>0) return `${h}h ${m}m ${sec}s`
  if(m>0) return `${m}m ${sec}s`
  return `${sec}s`
}

async function quantizeModel() {
  const model_id = document.getElementById('model').value
  const mode = document.getElementById('quant_mode').value
  const device = document.getElementById('device').value
  const bits = parseInt(document.getElementById('bits').value, 10)
  const weight_dtype = document.getElementById('weight_dtype').value
  const method = document.getElementById('method').value
  const range = document.getElementById('range').value
  const dataset = document.getElementById('dataset').value || null
  const activation_dtype = document.getElementById('activation_dtype').value
  const config = { bits, method, range, dataset, weight_dtype, activation_dtype }
  if(!(bits===8||bits===4)) { alert('bits must be 8 or 4'); return }
  const r = await fetch('/api/models/quantize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id, mode, device, config })
  })
  const j = await r.json()
  if (j.job_id) trackQuant(j.job_id)
}

async function trackQuant(job_id) {
  const div = document.getElementById('downloads')
  const bar = document.createElement('div')
  bar.className = 'progress'
  div.appendChild(bar)
  const tick = async () => {
    const r = await fetch('/api/models/quantize/status/' + job_id)
    const j = await r.json()
    if (j.status === 'completed' || j.status === 'error') {
      bar.textContent = j.status
      return
    }
    bar.textContent = j.status
    setTimeout(tick, 1000)
  }
  tick()
}

async function deleteModel() {
  const model_id = document.getElementById('model').value
  const r = await fetch('/api/models', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id })
  })
  await r.json()
  loadModels()
}

document.getElementById('lang').addEventListener('change', e => {
  lang = e.target.value
  i18n()
})
document.getElementById('refreshModels').addEventListener('click', loadModels)
document.getElementById('send').addEventListener('click', sendChat)
document.getElementById('download').addEventListener('click', downloadModel)
document.getElementById('quantize').addEventListener('click', quantizeModel)
document.getElementById('delete').addEventListener('click', deleteModel)

document.getElementById('save_preset').addEventListener('click', ()=>{
  const preset = {
    bits: document.getElementById('bits').value,
    method: document.getElementById('method').value,
    range: document.getElementById('range').value,
    dataset: document.getElementById('dataset').value
  }
  localStorage.setItem('quant_preset', JSON.stringify(preset))
  alert('Preset saved')
})
document.getElementById('load_preset').addEventListener('click', ()=>{
  const s = localStorage.getItem('quant_preset')
  if(!s) return alert('No preset')
  const p = JSON.parse(s)
  document.getElementById('bits').value = p.bits
  document.getElementById('method').value = p.method
  document.getElementById('range').value = p.range
  document.getElementById('dataset').value = p.dataset
})
document.getElementById('export_preset').addEventListener('click', ()=>{
  const preset = {
    bits: document.getElementById('bits').value,
    method: document.getElementById('method').value,
    range: document.getElementById('range').value,
    dataset: document.getElementById('dataset').value
  }
  const blob = new Blob([JSON.stringify(preset, null, 2)], {type:'application/json'})
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'quant_preset.json'
  a.click()
})
document.getElementById('import_preset').addEventListener('click', ()=>{
  document.getElementById('import_file').click()
})
document.getElementById('import_file').addEventListener('change', (e)=>{
  const f = e.target.files[0]
  if(!f) return
  const reader = new FileReader()
  reader.onload = ()=>{
    try{
      const p = JSON.parse(reader.result)
      if(!(p.bits==='8'||p.bits==='4'||p.bits===8||p.bits===4)) throw new Error('invalid bits')
      document.getElementById('bits').value = String(p.bits)
      document.getElementById('method').value = p.method
      document.getElementById('range').value = p.range
      document.getElementById('dataset').value = p.dataset||''
    }catch(err){ alert('Invalid preset '+err.message) }
  }
  reader.readAsText(f)
})

loadAccelerators()
loadModels()
loadSys()
i18n()