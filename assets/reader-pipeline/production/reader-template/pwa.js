(()=>{'use strict';
const button=document.getElementById('install-app'),dialog=document.getElementById('install-help'),instructions=document.getElementById('install-instructions');let prompt=null;
addEventListener('beforeinstallprompt',event=>{event.preventDefault();prompt=event;});
button?.addEventListener('click',async()=>{if(prompt){const pending=prompt;prompt=null;try{await pending.prompt();if((await pending.userChoice).outcome==='accepted')return;}catch{}}
instructions.textContent=/iPad|iPhone|iPod/.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1)?'Safari의 공유 메뉴에서 홈 화면에 추가를 선택하고 아이콘으로 실행하세요.':'브라우저 메뉴에서 앱 설치 또는 홈 화면에 추가를 선택하세요. 전체화면이 차단된 경우 설치한 앱으로 실행하세요.';dialog.showModal();});
document.getElementById('install-help-close')?.addEventListener('click',()=>dialog.close());
if('serviceWorker'in navigator)addEventListener('load',()=>navigator.serviceWorker.register('./sw.js',{scope:'./',updateViaCache:'none'}).catch(()=>{}));
})();
