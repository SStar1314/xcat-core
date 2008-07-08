Summary: Metapackage for a common, default xCAT setup
Name: xCAT
Version: 2.1
Release: snap%(date +"%Y%m%d%H%M")
License: EPL
Group: Applications/System
Vendor: IBM Corp.
Packager: IBM Corp.
Distribution: %{?_distribution:%{_distribution}}%{!?_distribution:%{_vendor}}
Prefix: /opt/xcat
BuildRoot: /var/tmp/%{name}-%{version}-%{release}-root
#BuildArch: noarch
Source1: xcat.conf
Source2: postscripts.tar.gz
Source3: templates.tar.gz

Provides: xCAT = %{version}
Requires: xCAT-server xCAT-client perl-DBD-SQLite

%ifos linux
Requires: atftp dhcp httpd nfs-utils expect conserver fping bind perl-XML-Parser vsftpd
%endif

%ifarch i386 i586 i686 x86 x86_64
Requires: xCAT-nbroot-oss-x86 xCAT-nbroot-core-x86 xCAT-nbkernel-x86 xCAT-nbroot-oss-x86_64 xCAT-nbroot-core-x86_64 xCAT-nbkernel-x86_64 syslinux
Requires: ipmitool >= 1.8.9
%endif

%description
xCAT is a server management package intended for at-scale management, including
hardware management and software management.

%prep
%ifos linux
tar zxf %{SOURCE2}
%else
rm -rf postscripts
cp %{SOURCE2} /opt/freeware/src/packages/BUILD
gunzip -f postscripts.tar.gz
tar -xf postscripts.tar
%endif

%build

%install
if [ -e /etc/SuSE-release ]; then
  apachedir=$RPM_BUILD_ROOT/etc/apache2/conf.d
else
  apachedir=$RPM_BUILD_ROOT/etc/httpd/conf.d
fi

mkdir -p $RPM_BUILD_ROOT/etc/apache2/conf.d
mkdir -p $RPM_BUILD_ROOT/etc/httpd/conf.d
mkdir -p $RPM_BUILD_ROOT/install/postscripts
mkdir -p $RPM_BUILD_ROOT/%{prefix}/share/xcat/
cd $RPM_BUILD_ROOT/%{prefix}/share/xcat/

%ifos linux
tar zxf %{SOURCE3}
%else
cp %{SOURCE3} $RPM_BUILD_ROOT/%{prefix}/share/xcat
gunzip -f templates.tar.gz
tar -xf templates.tar
rm templates.tar
%endif

cd -
cd $RPM_BUILD_ROOT/install

%ifos linux
tar zxf %{SOURCE2}
%else
cp %{SOURCE2} $RPM_BUILD_ROOT/install
gunzip -f postscripts.tar.gz
tar -xf postscripts.tar
rm postscripts.tar
%endif

rm LICENSE.html
mkdir -p postscripts/hostkeys
cd -
cp %{SOURCE1} $RPM_BUILD_ROOT/etc/apache2/conf.d/xcat.conf
cp %{SOURCE1} $RPM_BUILD_ROOT/etc/httpd/conf.d/xcat.conf

mkdir -p $RPM_BUILD_ROOT/%{prefix}/share/doc/packages/xCAT
cp LICENSE.html $RPM_BUILD_ROOT/%{prefix}/share/doc/packages/xCAT

%post
%ifnos linux
. /etc/profile
$RPM_INSTALL_PREFIX0/sbin/xcatconfig
%else
. /etc/profile.d/xcat.sh

if grep -i suse /etc/issue >/dev/null 2>&1; then
  apachename=apache2
else
  apachedir=httpd
fi

if [ ! -d /var/ftp/install ]; then
   mkdir -p /var/ftp/install
   echo "/install                /var/ftp/install        none  bind,defaults 0 0" >> /etc/fstab
   mount /var/ftp/install
fi

if [ ! -d /var/ftp/tftpboot ]; then 
   mkdir -p /var/ftp/tftpboot
   echo "/tftpboot   /var/ftp/tftpboot none bind,defaults 0 0" >> /etc/fstab
   mount /var/ftp/tftpboot
fi

if [ ! -f /install/postscripts/hostkeys/ssh_host_key ]; then
    echo Generating SSH1 RSA Key...
    /usr/bin/ssh-keygen -t rsa1 -f /install/postscripts/hostkeys/ssh_host_key -C '' -N ''
    echo Generating SSH2 RSA Key...
    /usr/bin/ssh-keygen -t rsa -f /install/postscripts/hostkeys/ssh_host_rsa_key -C '' -N ''
    echo Generating SSH2 DSA Key...
    /usr/bin/ssh-keygen -t dsa -f /install/postscripts/hostkeys/ssh_host_dsa_key -C '' -N ''
fi
if [ -d /install/postscripts/.ssh ]; then
   mv /install/postscripts/.ssh /install/postscripts/_ssh
fi
if [ -d /install/postscripts/.xcat ]; then
   mv /install/postscripts/.xcat /install/postscripts/_xcat
fi
chkconfig vsftpd on
/etc/rc.d/init.d/vsftpd start
if [ "$1" = "1" ]; then #Only if installing for the fist time..
    mkdir -p /root/.ssh
    chmod 700 /root/.ssh
    echo StrictHostKeyChecking no >> /root/.ssh/config
    chmod 600 /root/.ssh/config
    if [ ! -r /root/.ssh/id_rsa.pub ]; then
        ssh-keygen -t rsa -q -b 2048 -N "" -f /root/.ssh/id_rsa
    fi
    mkdir -p /install/postscripts/_ssh
    cp /root/.ssh/id_rsa.pub /install/postscripts/_ssh/authorized_keys

    mkdir -p /var/log/consoles
    if ! grep /tftpboot /etc/exports; then
        echo '/tftpboot *(rw,no_root_squash,sync)' >> /etc/exports #SECURITY: this has potential for sharing private host/user keys
    fi
    if ! grep /install /etc/exports; then
        echo '/install *(rw,no_root_squash,sync)' >> /etc/exports #SECURITY: this has potential for sharing private host/user keys
    fi
	chkconfig nfs on
	/etc/rc.d/init.d/nfs stop
	/etc/rc.d/init.d/nfs start
	exportfs -a
    if [ ! -r /etc/xcat/site.sqlite ]; then
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab key=xcatdport site.value=3001
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab key=xcatiport site.value=3002
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab key=tftpdir site.value=/tftpboot
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab key=master site.value=$(getent hosts `hostname`|awk '{print $1}')
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab key=domain site.value=$(hostname -d)
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab key=installdir site.value=/install
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab key=timezone site.value=`grep ^ZONE /etc/sysconfig/clock|cut -d= -f 2|sed -e 's/"//g'`
    fi
    if [ ! -r /etc/xcat/postscripts.sqlite ]; then
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab node=xcatdefaults postscripts.postscripts='syslog,remoteshell'
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab node=service postscripts.postscripts='servicenode'
    fi
    if [ ! -r /etc/xcat/policy.sqlite ]; then
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab priority=1 policy.name=root policy.rule=allow
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab priority=2 policy.commands=getbmcconfig policy.rule=allow
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab priority=3 policy.commands=nextdestiny policy.rule=allow
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab priority=4 policy.commands=getdestiny policy.rule=allow
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab priority=4.4 policy.commands=getpostscript policy.rule=allow
      XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab priority=4.5 policy.commands=getcredentials policy.rule=allow
    fi

    if [ ! -d /etc/xcat/ca ]; then
      yes | $RPM_INSTALL_PREFIX0/share/xcat/scripts/setup-xcat-ca.sh "xCAT CA"
    fi
    mkdir -p /install/postscripts/ca
    cp -r /etc/xcat/ca/* /install/postscripts/ca
    if [ ! -d /etc/xcat/cert ]; then
      yes | $RPM_INSTALL_PREFIX0/share/xcat/scripts/setup-server-cert.sh `hostname`
    fi
    mkdir -p /install/postscripts/cert
    cp -r /etc/xcat/cert/* /install/postscripts/cert
    if [ ! -r /root/.xcat/client-key.pem ]; then
      yes | $RPM_INSTALL_PREFIX0/share/xcat/scripts/setup-local-client.sh root
    fi
    mkdir -p /install/postscripts/_xcat
    cp -r /root/.xcat/* /install/postscripts/_xcat
    #Zap the almost certainly wrong pxelinux.cfg file
	if [ -r  /tftpboot/pxelinux.cfg/default ]
	then
    	rm /tftpboot/pxelinux.cfg/default
	fi
    # make Management Node
	touch /etc/xCATMN
	# setup syslog
        /install/postscripts/syslog
    #fi

    XCATROOT=$RPM_INSTALL_PREFIX0 /etc/init.d/xcatd start
    if [ -x $RPM_INSTALL_PREFIX0/sbin/mknb ]; then
%ifarch i386 i586 i686 x86 x86_64
       $RPM_INSTALL_PREFIX0/sbin/mknb x86
       $RPM_INSTALL_PREFIX0/sbin/mknb x86_64
%endif
%ifarch ppc ppc64
       $RPM_INSTALL_PREFIX0/sbin/mknb ppc64
%endif
    fi
    $RPM_INSTALL_PREFIX0/sbin/makenetworks
    XCATROOT=$RPM_INSTALL_PREFIX0 $RPM_INSTALL_PREFIX0/sbin/chtab key=nameservers site.value=`sed -e 's/#.*//' /etc/resolv.conf|grep nameserver|awk '{printf $2 ","}'|sed -e s/,$//`
    chkconfig $apachename on
	/etc/rc.d/init.d/$apachename stop
	/etc/rc.d/init.d/$apachename start
    echo "xCAT is now installed, it is recommended to tabedit networks and set a dynamic ip address range on any networks where nodes are to be discovered"
    echo "Then, run makedhcp -n to create a new dhcpd.configuration file, and /etc/init.d/dhcpd restart"
    echo "Either examine sample configuration templates, or write your own, or specify a value per node with nodeadd or tabedit."
fi
%endif

%clean

%files
%{prefix}
/etc/httpd/conf.d/xcat.conf
/etc/apache2/conf.d/xcat.conf
/install/postscripts
%defattr(-,root,root)
