# Fork of nvidia_shield_remote
<a href="https://github.com/stefan-sherwood/nvidia_shield_remote">nvidia_shield_remote</a> is a Python class for controlling Nvidia Shield over a network.  This project extends that work and adds a GUI to it.

![image](https://github.com/SDNick484/nvidia_shield_remote/blob/master/Nvidia%20Shield%20Remote.png)

## Prerequisites
<details>
<summary>
<b><a href="https://www.python.org/downloads/">Python 3.6</a> or higher with <a href="https://github.com/google/python-adb">python-adb</a> installed</b>
</summary>
<br/>
&emsp13;&emsp13;&emsp13; <b>Install Python</b>

&emsp13;&emsp13;&emsp13; Download and install Python from <a href="https://www.python.org/downloads/">here</a>

&emsp13;&emsp13;&emsp13; <b>Install python-adb</b>  
&emsp13;&emsp13;&emsp13; <code>pip install adb</code>
<br/>
</details>

<details>
<summary>
<b>Android Debug Bridge (adb) installed on your computer</b>
</summary>
<br/>
&emsp13;&emsp13;&emsp13; Download the install for <a href="https://developer.android.com/studio/releases/platform-tools.html">ADB here</a>.
</details>

<details>
<summary>
<b>Nvidia Shield in Developer Mode with Network Debugging turned on</b>
</summary>
<br/>
&emsp13;&emsp13;&emsp13; <b>Turn on developer mode</b><br/>
&emsp13;&emsp13;&emsp13; <i>Settings &rarr; About &rarr; Build </i> (click Build 7 times - "You are now a developer" message will pop up)
<br/><br/>

&emsp13;&emsp13;&emsp13; <b>Turn on Network debugging</b><br/>
&emsp13;&emsp13;&emsp13; <i>Settings &rarr; Developer Options &rarr; Network debugging </i>
<br/>
</details>

<details>
<summary>
<b>The IP address and debug port of your Nvidia Shield</b>
</summary>

<br/>
&emsp13;&emsp13;&emsp13; <b>Get the IP address and debug port</b><br/>
&emsp13;&emsp13;&emsp13; <i>Settings &rarr; Developer Options &rarr; Network debugging</i>
<br/>
&emsp13;&emsp13;&emsp13; Update the "SHIELD_IP_PORT" variable of nvidia_remote.py with the correct IP
</details>

<details>
<summary>
<b>Public and private adb keys</b>
</summary>
<br/>
&emsp13;&emsp13;&emsp13; <code>adb connect SHIELD:5555 # use the DNS name (or IP address) and Port from the previous step</code><br/><br/>
&emsp13;&emsp13;&emsp13; <i>A message will pop up on your Shield asking you to confirm the connection.</i><br/>
&emsp13;&emsp13;&emsp13; <i>Files <code>adbkey</code> and <code>adbkey.pub</code> will be added to the <code>.android</code> directory of your home folder<br/>

&emsp13;&emsp13;&emsp13; &emsp13;&emsp13;&emsp13; <b>Linux/Mac</b>: <code>~/.android</code><br/>
&emsp13;&emsp13;&emsp13; &emsp13;&emsp13;&emsp13; <b>Windows</b>: <code>/users/<i>\<username></i>/.android</code><br/><br/>
&emsp13;&emsp13;&emsp13; Copy these two files to the directory containing <code>nvidia.py</code>
</details>
</i>

