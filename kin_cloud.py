from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import requests
import json
import os

app = FastAPI()

OPENROUTER_API_KEY = "PASTE_YOUR_KEY_HERE"
MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_memory(mem):
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>K.I.N</title>

<style>
body{
margin:0;
font-family:Segoe UI;
background:linear-gradient(135deg,#2563eb,#fde047);
height:100vh;
display:flex;
justify-content:center;
align-items:center;
}

#app{
width:390px;
height:80vh;
background:rgba(255,255,255,0.15);
backdrop-filter:blur(20px);
border-radius:25px;
display:flex;
flex-direction:column;
padding:15px;
}

#chat{flex:1;overflow:auto;color:white;}

.msg{margin-bottom:10px;}

img{max-width:180px;border-radius:12px;margin-top:5px;}

#controls{display:flex;gap:5px;}

input[type=text]{flex:1;padding:10px;border-radius:10px;border:none;}

button{padding:10px;border:none;border-radius:10px;background:#1d4ed8;color:white;}
</style>
</head>

<body>
<div id="app">
<div id="chat"></div>

<div id="controls">
<input id="msg">
<input type="file" id="img">
<button onclick="send()">Send</button>
</div>
</div>

<script>
const chat=document.getElementById("chat");

function add(sender,text,image){
let div=document.createElement("div");
div.className="msg";
div.innerHTML="<b>"+sender+":</b> "+text;
if(image){
let im=document.createElement("img");
im.src=image;
div.appendChild(im);
}
chat.appendChild(div);
chat.scrollTop=chat.scrollHeight;
}

async function send(){
let msg=document.getElementById("msg").value;
let file=document.getElementById("img").files[0];

let imgData=null;

if(file){
let reader=new FileReader();
reader.onload=()=>{imgData=reader.result; sendNow(msg,imgData);};
reader.readAsDataURL(file);
}else{
sendNow(msg,null);
}

add("You",msg,imgData);
document.getElementById("msg").value="";
document.getElementById("img").value="";
}

async function sendNow(msg,img){
let res=await fetch("/ask",{method:"POST",headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,image:img})});
let data=await res.json();
add("KIN",data.response);
speak(data.response);
}

function speak(text){
let speech=new SpeechSynthesisUtterance(text);
speech.lang="en-US";
speechSynthesis.speak(speech);
}
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_PAGE

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    message = data.get("message", "")
    image = data.get("image")

    memory = load_memory()

    content = [{"type":"text","text":message}]

    if image:
        content.append({
            "type":"image_url",
            "image_url":{"url":image}
        })

    memory.append({"role":"user","content":content})

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [{"role":"system","content":"You are K.I.N, a loyal intelligent AI companion."}] + memory[-10:]
        }
    )

    reply = response.json()["choices"][0]["message"]["content"]

    memory.append({"role":"assistant","content":reply})
    save_memory(memory)

    return JSONResponse({"response": reply})
