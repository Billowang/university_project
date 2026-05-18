import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from flask import Flask, request, jsonify
import threading
import time

class UltimateJoystickNode(Node):
    def __init__(self):
        super().__init__('ultimate_joystick_node')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # 狀態變數
        self.is_active = False
        self.last_rx = time.time()
        self.SAFE_LIMIT = 5000.0
        
        # 加速度平滑化變數
        self.target_v = 0.0
        self.target_w = 0.0
        self.current_v = 0.0
        self.current_w = 0.0
        self.max_rpm = 0.0
        
        # 設定：加速度限制（每 0.1 秒允許改變的最大比例，0.2 代表 20%）
        self.ramp_step = 0.15 

        # Timer 1: 監控連線安全 (Watchdog)
        self.create_timer(0.5, self.watchdog)
        
        # Timer 2: 平滑發送指令 (這解決了撞牆問題)
        self.create_timer(0.1, self.smooth_publish_loop)

    def watchdog(self):
        # 如果超過 1 秒沒收到網頁訊號，強制將目標設為 0
        if self.is_active and (time.time() - self.last_rx > 1.0):
            self.get_logger().warn("Watchdog triggered: Signal lost!")
            self.target_v = 0.0
            self.target_w = 0.0

    def smooth_publish_loop(self):
        """ 平滑化邏輯：讓 current_v 慢慢靠近 target_v """
        if not self.is_active:
            self.current_v, self.current_w = 0.0, 0.0
        else:
            # 處理線性速度 v
            diff_v = self.target_v - self.current_v
            if abs(diff_v) > self.ramp_step:
                self.current_v += self.ramp_step if diff_v > 0 else -self.ramp_step
            else:
                self.current_v = self.target_v

            # 處理轉向速度 w
            diff_w = self.target_w - self.current_w
            if abs(diff_w) > self.ramp_step:
                self.current_w += self.ramp_step if diff_w > 0 else -self.ramp_step
            else:
                self.current_w = self.target_w

        # 正式發布指令
        msg = Twist()
        msg.linear.x = float(self.current_v)
        msg.angular.z = float(self.current_w)
        msg.linear.z = float(self.max_rpm)
        self.publisher_.publish(msg)

    def update_targets(self, v, w, web_max, active):
        self.is_active = active
        self.last_rx = time.time()
        try:
            self.max_rpm = min(float(web_max), self.SAFE_LIMIT)
            if self.is_active:
                self.target_v = float(v)
                self.target_w = float(w)
            else:
                self.target_v, self.target_w = 0.0, 0.0
        except:
            self.target_v, self.target_w = 0.0, 0.0

# --- Flask Server 部分 ---
app = Flask(__name__)
ros_node = None

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script>
    !function(t,i){"object"==typeof exports&&"object"==typeof module?module.exports=i():"function"==typeof define&&define.amd?define("nipplejs",[],i):"object"==typeof exports?exports.nipplejs=i():t.nipplejs=i()}(window,function(){return e=[function(t,i,e){"use strict";e.r(i);function v(t,i){var e=i.x-t.x,i=i.y-t.y;return Math.sqrt(e*e+i*i)}function b(t){return t*(Math.PI/180)}function n(t){f.has(t)&&clearTimeout(f.get(t)),f.set(t,setTimeout(t,100))}function s(t,i,e){for(var o,n=i.split(/[ ,]+/g),s=0;s<n.length;s+=1)o=n[s],t.addEventListener?t.addEventListener(o,e,!1):t.attachEvent&&t.attachEvent(o,e)}function o(t,i,e){for(var o,n=i.split(/[ ,]+/g),s=0;s<n.length;s+=1)o=n[s],t.removeEventListener?t.removeEventListener(o,e):t.detachEvent&&t.detachEvent(o,e)}function r(t){return t.preventDefault(),t.type.match(/^touch/)?t.changedTouches:t}function d(){return{x:void 0!==window.pageXOffset?window.pageXOffset:(document.documentElement||document.body.parentNode||document.body).scrollLeft,y:void 0!==window.pageYOffset?window.pageYOffset:(document.documentElement||document.body.parentNode||document.body).scrollTop}}function p(t,i){i.top||i.right||i.bottom||i.left?(t.style.top=i.top,t.style.right=i.right,t.style.bottom=i.bottom,t.style.left=i.left):(t.style.left=i.x+"px",t.style.top=i.y+"px")}function a(t,i,e){var o,n=c(t);for(o in n)if(n.hasOwnProperty(o))if("string"==typeof i)n[o]=i+" "+e;else{for(var s="",r=0,d=i.length;r<d;r+=1)s+=i[r]+" "+e+", ";n[o]=s.slice(0,-2)}return n}function c(i){var e={};return e[i]="",["webkit","Moz","o"].forEach(function(t){e[t+i.charAt(0).toUpperCase()+i.slice(1)]=""}),e}function l(t,i){for(var e in i)i.hasOwnProperty(e)&&(t[e]=i[e])}function h(t,i){if(t.length)for(var e=0,o=t.length;e<o;e+=1)i(t[e]);else i(t)}var u,f=new Map,e=!!("ontouchstart"in window),y=!!window.PointerEvent,m=!!window.MSPointerEvent,g={start:"mousedown",move:"mousemove",end:"mouseup"},x={};function O(){}y?u={start:"pointerdown",move:"pointermove",end:"pointerup, pointercancel"}:m?u={start:"MSPointerDown",move:"MSPointerMove",end:"MSPointerUp"}:e?(u={start:"touchstart",move:"touchmove",end:"touchend, touchcancel"},x=g):u=g,O.prototype.on=function(t,i){var e,o=t.split(/[ ,]+/g);this._handlers_=this._handlers_||{};for(var n=0;n<o.length;n+=1)e=o[n],this._handlers_[e]=this._handlers_[e]||[],this._handlers_[e].push(i);return this},O.prototype.off=function(t,i){return this._handlers_=this._handlers_||{},void 0===t?this._handlers_={}:void 0===i?this._handlers_[t]=null:this._handlers_[t]&&0<=this._handlers_[t].indexOf(i)&&this._handlers_[t].splice(this._handlers_[t].indexOf(i),1),this},O.prototype.trigger=function(t,i){var e,o=this,n=t.split(/[ ,]+/g);o._handlers_=o._handlers_||{};for(var s=0;s<n.length;s+=1)e=n[s],o._handlers_[e]&&o._handlers_[e].length&&o._handlers_[e].forEach(function(t){t.call(o,{type:e,target:o},i)})},O.prototype.config=function(t){this.options=this.defaults||{},t&&(this.options=function(t,i){var e,o={};for(e in t)t.hasOwnProperty(e)&&i.hasOwnProperty(e)?o[e]=i[e]:t.hasOwnProperty(e)&&(o[e]=t[e]);return o}(this.options,t))},O.prototype.bindEvt=function(t,i){var e=this;return e._domHandlers_=e._domHandlers_||{},e._domHandlers_[i]=function(){"function"==typeof e["on"+i]?e["on"+i].apply(e,arguments):console.warn('[WARNING] : Missing "on'+i+'" handler.')},s(t,u[i],e._domHandlers_[i]),x[i]&&s(t,x[i],e._domHandlers_[i]),e},O.prototype.unbindEvt=function(t,i){return this._domHandlers_=this._domHandlers_||{},o(t,u[i],this._domHandlers_[i]),x[i]&&o(t,x[i],this._domHandlers_[i]),delete this._domHandlers_[i],this};y=O;function w(t,i){return this.identifier=i.identifier,this.position=i.position,this.frontPosition=i.frontPosition,this.collection=t,this.defaults={size:100,threshold:.1,color:"white",fadeTime:250,dataOnly:!1,restJoystick:!0,restOpacity:.5,mode:"dynamic",zone:document.body,lockX:!1,lockY:!1,shape:"circle"},this.config(i),"dynamic"===this.options.mode&&(this.options.restOpacity=0),this.id=w.id,w.id+=1,this.buildEl().stylize(),this.instance={el:this.ui.el,on:this.on.bind(this),off:this.off.bind(this),show:this.show.bind(this),hide:this.hide.bind(this),add:this.addToDom.bind(this),remove:this.removeFromDom.bind(this),destroy:this.destroy.bind(this),setPosition:this.setPosition.bind(this),resetDirection:this.resetDirection.bind(this),computeDirection:this.computeDirection.bind(this),trigger:this.trigger.bind(this),position:this.position,frontPosition:this.frontPosition,ui:this.ui,identifier:this.identifier,id:this.id,options:this.options},this.instance}w.prototype=new y,(w.constructor=w).id=0,w.prototype.buildEl=function(t){return this.ui={},this.options.dataOnly||(this.ui.el=document.createElement("div"),this.ui.back=document.createElement("div"),this.ui.front=document.createElement("div"),this.ui.el.className="nipple collection_"+this.collection.id,this.ui.back.className="back",this.ui.front.className="front",this.ui.el.setAttribute("id","nipple_"+this.collection.id+"_"+this.id),this.ui.el.appendChild(this.ui.back),this.ui.el.appendChild(this.ui.front)),this},w.prototype.stylize=function(){if(this.options.dataOnly)return this;var t=this.options.fadeTime+"ms",i=function(){var t,i=c("borderRadius");for(t in i)i.hasOwnProperty(t)&&(i[t]="50%");return i}(),t=a("transition","opacity",t),e={};return e.el={position:"absolute",opacity:this.options.restOpacity,display:"block",zIndex:999},e.back={position:"absolute",display:"block",width:this.options.size+"px",height:this.options.size+"px",marginLeft:-this.options.size/2+"px",marginTop:-this.options.size/2+"px",background:this.options.color,opacity:".5"},e.front={width:this.options.size/2+"px",height:this.options.size/2+"px",position:"absolute",display:"block",marginLeft:-this.options.size/4+"px",marginTop:-this.options.size/4+"px",background:this.options.color,opacity:".5",transform:"translate(0px, 0px)"},l(e.el,t),"circle"===this.options.shape&&l(e.back,i),l(e.front,i),this.applyStyles(e),this},w.prototype.applyStyles=function(t){for(var i in this.ui)if(this.ui.hasOwnProperty(i))for(var e in t[i])this.ui[i].style[e]=t[i][e];return this},w.prototype.addToDom=function(){return this.options.dataOnly||document.body.contains(this.ui.el)||this.options.zone.appendChild(this.ui.el),this},w.prototype.removeFromDom=function(){return!this.options.dataOnly&&document.body.contains(this.ui.el)&&this.options.zone.removeChild(this.ui.el),this},w.prototype.destroy=function(){clearTimeout(this.removeTimeout),clearTimeout(this.showTimeout),clearTimeout(this.restTimeout),this.trigger("destroyed",this.instance),this.removeFromDom(),this.off()},w.prototype.show=function(t){var i=this;return i.options.dataOnly||(clearTimeout(i.removeTimeout),clearTimeout(i.showTimeout),clearTimeout(i.restTimeout),i.addToDom(),i.restCallback(),setTimeout(function(){i.ui.el.style.opacity=1},0),i.showTimeout=setTimeout(function(){i.trigger("shown",i.instance),"function"==typeof t&&t.call(this)},i.options.fadeTime)),i},w.prototype.hide=function(i){var t,e,o=this;return o.options.dataOnly||(o.ui.el.style.opacity=o.options.restOpacity,clearTimeout(o.removeTimeout),clearTimeout(o.showTimeout),clearTimeout(o.restTimeout),o.removeTimeout=setTimeout(function(){var t="dynamic"===o.options.mode?"none":"block";o.ui.el.style.display=t,"function"==typeof i&&i.call(o),o.trigger("hidden",o.instance)},o.options.fadeTime),o.options.restJoystick&&(t=o.options.restJoystick,(e={}).x=!0===t||!1!==t.x?0:o.instance.frontPosition.x,e.y=!0===t||!1!==t.y?0:o.instance.frontPosition.y,o.setPosition(i,e))),o},w.prototype.setPosition=function(t,i){var e=this,i=(e.frontPosition={x:i.x,y:i.y},e.options.fadeTime+"ms"),o={},i=(o.front=a("transition",["transform"],i),{front:{}});i.front={transform:"translate("+e.frontPosition.x+"px,"+e.frontPosition.y+"px)"},e.applyStyles(o),e.applyStyles(i),e.restTimeout=setTimeout(function(){"function"==typeof t&&t.call(e),e.restCallback()},e.options.fadeTime)},w.prototype.restCallback=function(){var t={};t.front=a("transition","none",""),this.applyStyles(t),this.trigger("rested",this.instance)},w.prototype.resetDirection=function(){this.direction={x:!1,y:!1,angle:!1}},w.prototype.computeDirection=function(t){var i,e,o,n=t.angle.radian,s=Math.PI/4,r=Math.PI/2;if(s<n&&n<3*s&&!t.lockX?i="up":-s<n&&n<=s&&!t.lockY?i="left":3*-s<n&&n<=-s&&!t.lockX?i="down":t.lockY||(i="right"),t.lockY||(e=-r<n&&n<r?"left":"right"),t.lockX||(o=0<n?"up":"down"),t.force>this.options.threshold){var d,p={};for(d in this.direction)this.direction.hasOwnProperty(d)&&(p[d]=this.direction[d]);var a={};for(d in this.direction={x:e,y:o,angle:i},t.direction=this.direction,p)p[d]===this.direction[d]&&(a[d]=!0);if(a.x&&a.y&&a.angle)return t;a.x&&a.y||this.trigger("plain",t),a.x||this.trigger("plain:"+e,t),a.y||this.trigger("plain:"+o,t),a.angle||this.trigger("dir dir:"+i,t)}else this.resetDirection();return t};var _=w;function T(t,i){this.nipples=[],this.idles=[],this.actives=[],this.ids=[],this.pressureIntervals={},this.manager=t,this.id=T.id,T.id+=1,this.defaults={zone:document.body,multitouch:!1,maxNumberOfNipples:10,mode:"dynamic",position:{top:0,left:0},catchDistance:200,size:100,threshold:.1,color:"white",fadeTime:250,dataOnly:!1,restJoystick:!0,restOpacity:.5,lockX:!1,lockY:!1,shape:"circle",dynamicPage:!1,follow:!1},this.config(i),"static"!==this.options.mode&&"semi"!==this.options.mode||(this.options.multitouch=!1),this.options.multitouch||(this.options.maxNumberOfNipples=1);t=getComputedStyle(this.options.zone.parentElement);return t&&"flex"===t.display&&(this.parentIsFlex=!0),this.updateBox(),this.prepareNipples(),this.bindings(),this.begin(),this.nipples}T.prototype=new y,(T.constructor=T).id=0,T.prototype.prepareNipples=function(){var o=this.nipples;o.on=this.on.bind(this),o.off=this.off.bind(this),o.options=this.options,o.destroy=this.destroy.bind(this),o.ids=this.ids,o.id=this.id,o.processOnMove=this.processOnMove.bind(this),o.processOnEnd=this.processOnEnd.bind(this),o.get=function(t){if(void 0===t)return o[0];for(var i=0,e=o.length;i<e;i+=1)if(o[i].identifier===t)return o[i];return!1}},T.prototype.bindings=function(){this.bindEvt(this.options.zone,"start"),this.options.zone.style.touchAction="none",this.options.zone.style.msTouchAction="none"},T.prototype.begin=function(){var t=this.options;"static"===t.mode&&((t=this.createNipple(t.position,this.manager.getIdentifier())).add(),this.idles.push(t))},T.prototype.createNipple=function(t,i){var e=this.manager.scroll,o={},n=this.options,s=this.parentIsFlex?e.x:e.x+this.box.left,r=this.parentIsFlex?e.y:e.y+this.box.top,s=(t.x&&t.y?o={x:t.x-s,y:t.y-r}:(t.top||t.right||t.bottom||t.left)&&((s=document.createElement("DIV")).style.display="hidden",s.style.top=t.top,s.style.right=t.right,s.style.bottom=t.bottom,s.style.left=t.left,s.style.position="absolute",n.zone.appendChild(s),r=s.getBoundingClientRect(),n.zone.removeChild(s),o=t,t={x:r.left+e.x,y:r.top+e.y}),new _(this,{color:n.color,size:n.size,threshold:n.threshold,fadeTime:n.fadeTime,dataOnly:n.dataOnly,restJoystick:n.restJoystick,restOpacity:n.restOpacity,mode:n.mode,identifier:i,position:t,zone:n.zone,frontPosition:{x:0,y:0},shape:n.shape}));return n.dataOnly||(p(s.ui.el,o),p(s.ui.front,s.frontPosition)),this.nipples.push(s),this.trigger("added "+s.identifier+":added",s),this.manager.trigger("added "+s.identifier+":added",s),this.bindNipple(s),s},T.prototype.updateBox=function(){this.box=this.options.zone.getBoundingClientRect()},T.prototype.bindNipple=function(t){function i(t,i){e=t.type+" "+i.id+":"+t.type,o.trigger(e,i)}var e,o=this;t.on("destroyed",o.onDestroyed.bind(o)),t.on("shown hidden rested dir plain",i),t.on("dir:up dir:right dir:down dir:left",i),t.on("plain:up plain:right plain:down plain:left",i)},T.prototype.pressureFn=function(i,e,t){var o=this,n=0;clearInterval(o.pressureIntervals[t]),o.pressureIntervals[t]=setInterval(function(){var t=i.force||i.pressure||i.webkitForce||0;t!==n&&(e.trigger("pressure",t),o.trigger("pressure "+e.identifier+":pressure",t),n=t)}.bind(o),100)},T.prototype.onstart=function(e){var o=this,i=o.options,n=e;return e=r(e),o.updateBox(),h(e,function(t){o.actives.length<i.maxNumberOfNipples?o.processOnStart(t):n.type.match(/^touch/)&&(Object.keys(o.manager.ids).forEach(function(i){var t;Object.values(n.touches).findIndex(function(t){return t.identifier===i})<0&&((t=[e[0]]).identifier=i,o.processOnEnd(t))}),o.actives.length<i.maxNumberOfNipples&&o.processOnStart(t))}),o.manager.bindDocument(),!1},T.prototype.processOnStart=function(i){function t(t){t.trigger("start",t),e.trigger("start "+t.id+":start",t),t.show(),0<s&&e.pressureFn(i,t,t.identifier),e.processOnMove(i)}var e=this,o=e.options,n=e.manager.getIdentifier(i),s=i.force||i.pressure||i.webkitForce||0,r={x:i.pageX,y:i.pageY},d=e.getOrCreate(n,r);d.identifier!==n&&e.manager.removeIdentifier(d.identifier),d.identifier=n;if(0<=(n=e.idles.indexOf(d))&&e.idles.splice(n,1),e.actives.push(d),e.ids.push(d.identifier),"semi"!==o.mode)t(d);else{if(!(v(r,d.position)<=o.catchDistance))return d.destroy(),void e.processOnStart(i);t(d)}return d},T.prototype.getOrCreate=function(t,i){var e,o=this.options;return/(semi|static)/.test(o.mode)?(e=this.idles[0])?(this.idles.splice(0,1),e):"semi"===o.mode?this.createNipple(i,t):(console.warn("Coudln't find the needed nipple."),!1):this.createNipple(i,t)},T.prototype.processOnMove=function(t){var i=this.options,e=this.manager.getIdentifier(t),o=this.nipples.get(e),n=this.manager.scroll;if(s=t,isNaN(s.buttons)?0!==s.pressure:0!==s.buttons){if(!o)return console.error("Found zombie joystick with ID "+e),void this.manager.removeIdentifier(e);i.dynamicPage&&(s=o.el.getBoundingClientRect(),o.position={x:n.x+s.left,y:n.y+s.top}),o.identifier=e;var s=o.options.size/2,e={x:t.pageX,y:t.pageY};i.lockX&&(e.y=o.position.y),i.lockY&&(e.x=o.position.x);var r,d,p,a,c,l=v(e,o.position),h=(h=e,u=o.position,f=u.x-h.x,u=u.y-h.y,Math.atan2(u,f)*(180/Math.PI)),u=b(h),f=l/s,y={distance:l,position:e},m=("circle"===o.options.shape?(r=Math.min(l,s),d=o.position,p=r,c={x:0,y:0},a=b(h),c.x=d.x-p*Math.cos(a),c.y=d.y-p*Math.sin(a),d=c):(p=e,a=o.position,c=s,d={x:Math.min(Math.max(p.x,a.x-c),a.x+c),y:Math.min(Math.max(p.y,a.y-c),a.y+c)},r=v(d,o.position)),i.follow?s<l&&(m=e.x-d.x,g=e.y-d.y,o.position.x+=m,o.position.y+=g,o.el.style.top=o.position.y-(this.box.top+n.y)+"px",o.el.style.left=o.position.x-(this.box.left+n.x)+"px",l=v(e,o.position)):(e=d,l=r),e.x-o.position.x),g=e.y-o.position.y,n=(o.frontPosition={x:m,y:g},i.dataOnly||(o.ui.front.style.transform="translate("+m+"px,"+g+"px)"),{identifier:o.identifier,position:e,force:f,pressure:t.force||t.pressure||t.webkitForce||0,distance:l,angle:{radian:u,degree:h},vector:{x:m/s,y:-g/s},raw:y,instance:o,lockX:i.lockX,lockY:i.lockY});(n=o.computeDirection(n)).angle={radian:b(180-h),degree:180-h},o.trigger("move",n),this.trigger("move "+o.id+":move",n)}else this.processOnEnd(t)},T.prototype.processOnEnd=function(t){var i=this,e=i.options,t=i.manager.getIdentifier(t),o=i.nipples.get(t),t=i.manager.removeIdentifier(o.identifier);o&&(e.dataOnly||o.hide(function(){"dynamic"===e.mode&&(o.trigger("removed",o),i.trigger("removed "+o.id+":removed",o),i.manager.trigger("removed "+o.id+":removed",o),o.destroy())}),clearInterval(i.pressureIntervals[o.identifier]),o.resetDirection(),o.trigger("end",o),i.trigger("end "+o.id+":end",o),0<=i.ids.indexOf(o.identifier)&&i.ids.splice(i.ids.indexOf(o.identifier),1),0<=i.actives.indexOf(o)&&i.actives.splice(i.actives.indexOf(o),1),/(semi|static)/.test(e.mode)?i.idles.push(o):0<=i.nipples.indexOf(o)&&i.nipples.splice(i.nipples.indexOf(o),1),i.manager.unbindDocument(),/(semi|static)/.test(e.mode)&&(i.manager.ids[t.id]=t.identifier))},T.prototype.onDestroyed=function(t,i){0<=this.nipples.indexOf(i)&&this.nipples.splice(this.nipples.indexOf(i),1),0<=this.actives.indexOf(i)&&this.actives.splice(this.actives.indexOf(i),1),0<=this.idles.indexOf(i)&&this.idles.splice(this.idles.indexOf(i),1),0<=this.ids.indexOf(i.identifier)&&this.ids.splice(this.ids.indexOf(i.identifier),1),this.manager.removeIdentifier(i.identifier),this.manager.unbindDocument()},T.prototype.destroy=function(){for(var t in this.unbindEvt(this.options.zone,"start"),this.nipples.forEach(function(t){t.destroy()}),this.pressureIntervals)this.pressureIntervals.hasOwnProperty(t)&&clearInterval(this.pressureIntervals[t]);this.trigger("destroyed",this.nipples),this.manager.unbindDocument(),this.off()};var k=T;function P(t){function i(){var i;o.collections.forEach(function(t){t.forEach(function(t){i=t.el.getBoundingClientRect(),t.position={x:o.scroll.x+i.left,y:o.scroll.y+i.top}})})}function e(){o.scroll=d()}var o=this;o.ids={},o.index=0,o.collections=[],o.scroll=d(),o.config(t),o.prepareCollections(),s(window,"resize",function(){n(i)});return s(window,"scroll",function(){n(e)}),o.collections}P.prototype=new y,(P.constructor=P).prototype.prepareCollections=function(){var t=this;t.collections.create=t.create.bind(t),t.collections.on=t.on.bind(t),t.collections.off=t.off.bind(t),t.collections.destroy=t.destroy.bind(t),t.collections.get=function(i){var e;return t.collections.every(function(t){return!(e=t.get(i))}),e}},P.prototype.create=function(t){return this.createCollection(t)},P.prototype.createCollection=function(t){t=new k(this,t);return this.bindCollection(t),this.collections.push(t),t},P.prototype.bindCollection=function(t){function i(t,i){e=t.type+" "+i.id+":"+t.type,o.trigger(e,i)}var e,o=this;t.on("destroyed",o.onDestroyed.bind(o)),t.on("shown hidden rested dir plain",i),t.on("dir:up dir:right dir:down dir:left",i),t.on("plain:up plain:right plain:down plain:left",i)},P.prototype.bindDocument=function(){this.binded||(this.bindEvt(document,"move").bindEvt(document,"end"),this.binded=!0)},P.prototype.unbindDocument=function(t){Object.keys(this.ids).length&&!0!==t||(this.unbindEvt(document,"move").unbindEvt(document,"end"),this.binded=!1)},P.prototype.getIdentifier=function(t){var i;return t?void 0===(i=void 0===t.identifier?t.pointerId:t.identifier)&&(i=this.latest||0):i=this.index,void 0===this.ids[i]&&(this.ids[i]=this.index,this.index+=1),this.latest=i,this.ids[i]},P.prototype.removeIdentifier=function(t){var i,e={};for(i in this.ids)if(this.ids[i]===t){e.id=i,e.identifier=this.ids[i],delete this.ids[i];break}return e},P.prototype.onmove=function(t){return this.onAny("move",t),!1},P.prototype.onend=function(t){return this.onAny("end",t),!1},P.prototype.oncancel=function(t){return this.onAny("end",t),!1},P.prototype.onAny=function(t,i){var e,o=this,n="processOn"+t.charAt(0).toUpperCase()+t.slice(1);i=r(i);return h(i,function(t){e=o.getIdentifier(t),h(o.collections,function(t,i,e){0<=e.ids.indexOf(i)&&(e[n](t),t._found_=!0)}.bind(null,t,e)),t._found_||o.removeIdentifier(e)}),!1},P.prototype.destroy=function(){this.unbindDocument(!0),this.ids={},this.index=0,this.collections.forEach(function(t){t.destroy()}),this.off()},P.prototype.onDestroyed=function(t,i){if(this.collections.indexOf(i)<0)return!1;this.collections.splice(this.collections.indexOf(i),1)};var E=new P;i.default={create:function(t){return E.create(t)},factory:E}}],o={},n.m=e,n.c=o,n.d=function(t,i,e){n.o(t,i)||Object.defineProperty(t,i,{enumerable:!0,get:e})},n.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},n.t=function(i,t){if(1&t&&(i=n(i)),8&t)return i;if(4&t&&"object"==typeof i&&i&&i.__esModule)return i;var e=Object.create(null);if(n.r(e),Object.defineProperty(e,"default",{enumerable:!0,value:i}),2&t&&"string"!=typeof i)for(var o in i)n.d(e,o,function(t){return i[t]}.bind(null,o));return e},n.n=function(t){var i=t&&t.__esModule?function(){return t.default}:function(){return t};return n.d(i,"a",i),i},n.o=function(t,i){return Object.prototype.hasOwnProperty.call(t,i)},n.p="",n(n.s=0).default;function n(t){if(o[t])return o[t].exports;var i=o[t]={i:t,l:!1,exports:{}};return e[t].call(i.exports,i,i.exports,n),i.l=!0,i.exports}var e,o});
    </script>
    <style>
        html, body {
            touch-action: none; 
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            -khtml-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
            -webkit-tap-highlight-color: transparent;
            outline: none;
        }
        a, button, input, textarea, select, div {
            -webkit-tap-highlight-color: transparent;
            outline: none;
        }
        body { background: #0f0f0f; color: #fff; font-family: sans-serif; margin: 0; overflow: hidden; text-align: center; }
        .status-bar { width: 100%; height: 50px; line-height: 50px; font-weight: bold; background: #c0392b; transition: 0.3s; }
        .active { background: #27ae60; }
        .control-panel { background: #1a1a1a; padding: 20px; border-bottom: 1px solid #333; }
        .num { font-size: 30px; color: #00ffcc; font-family: monospace; }
        #zone { width: 100vw; height: 60vh; position: relative; }
        button { padding: 15px 30px; font-size: 18px; border-radius: 8px; border: none; cursor: pointer; }
        #start { background: #2ecc71; color: #white; }
        #stop { background: #e74c3c; color: #white; }
    </style>
</head>
<body>
    <div id="status" class="status-bar">LOCKED</div>
    <div class="control-panel">
        <button id="start" onclick="setMode(true)">ENABLE</button>
        <button id="stop" onclick="setMode(false)">DISABLE</button>
        <div style="margin-top:10px;">MAX RPM: <input type="number" id="max_in" value="2000" style="width:80px;"></div>
    </div>
    <div style="display:flex; justify-content: space-around; padding: 10px;">
        <div>L: <span id="l_val" class="num">0</span></div>
        <div>R: <span id="r_val" class="num">0</span></div>
    </div>
    <div id="zone"></div>

    <script>
        let active = false;
        let curV = 0, curW = 0;
        const statusDiv = document.getElementById('status');

        document.addEventListener('touchstart', function (event) {
    if (event.touches.length > 1) {
       
    }
}, { passive: false });

let lastTouchEnd = 0;
document.addEventListener('touchend', function (event) {
    const now = (new Date()).getTime();
    
    if (now - lastTouchEnd <= 300) {
        event.preventDefault();
    }
    lastTouchEnd = now;
}, false);


document.addEventListener('gesturestart', function (event) {
    event.preventDefault();
});

        function setMode(s) {
            active = s;
            statusDiv.innerText = active ? "ACTIVE" : "LOCKED";
            statusDiv.className = "status-bar" + (active ? " active" : "");
            if(!active) { curV = 0; curW = 0; }
        }

        const joy = nipplejs.create({
            zone: document.getElementById('zone'),
            mode: 'static', position: {left: '50%', top: '50%'},
            color: '#3498db', size: 200
        });

        joy.on('move', (e, d) => {
            if(!active) return;
            curV = d.vector.y;
            curW = -d.vector.x;
            updateUI(curV, curW);
        });

        joy.on('end', () => {
            curV = 0; curW = 0;
            updateUI(0, 0);
        });

        function updateUI(v, w) {
            let max = document.getElementById('max_in').value;
            document.getElementById('l_val').innerText = Math.round((v - w*0.5) * max);
            document.getElementById('r_val').innerText = Math.round((v + w*0.5) * max);
        }

        // --- 核心改進：定時心跳包 ---
        // 每 100ms 不管搖桿有沒有動，都向 ROS 報告一次狀態
        setInterval(() => {
            let limit = document.getElementById('max_in').value;
            fetch(`/joy?v=${curV.toFixed(2)}&w=${curW.toFixed(2)}&max=${limit}&act=${active}`).catch(()=>{});
        }, 100);
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return HTML

@app.route('/joy')
def joy():
    v = request.args.get('v', 0.0)
    w = request.args.get('w', 0.0)
    m = request.args.get('max', 0.0)
    a = request.args.get('act', 'false') == 'true'
    if ros_node: ros_node.update_targets(v, w, m, a)
    return jsonify(ok=True)

def main():
    global ros_node
    rclpy.init()
    ros_node = UltimateJoystickNode()
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    try: rclpy.spin(ros_node)
    except: rclpy.shutdown()

if __name__ == '__main__': main()
