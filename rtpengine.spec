Name:		rtpengine
Version:	6.4.2.1
Release:	1%{?dist}
Summary:	The Sipwise NGCP rtpengine

Group:		System Environment/Daemons
License:	GPLv3
URL:		  https://github.com/sipwise/rtpengine
Source0:	https://github.com/sipwise/rtpengine/archive/mr%{version}/%{name}-mr%{version}.tar.gz
Source1:  rtpengine.service
Source2:  rtpengine.tmpfiles
Source3:  rtpengine-iptables-setup
Source4:  rtpengine-recording.service
Source5:  rtpengine-recording-nfs-setup
Conflicts:	%{name}-kernel < %{version}-%{release}

%global with_transcoding 1

BuildRequires:	gcc make pkgconfig redhat-rpm-config
BuildRequires:	glib2-devel libcurl-devel openssl-devel pcre-devel
BuildRequires:	xmlrpc-c-devel zlib-devel hiredis-devel
BuildRequires:	libpcap-devel libevent-devel json-glib-devel
%if 0%{?rhel} == 7
BuildRequires:  systemd
%endif
BuildRequires:  bcg729-devel
Requires(pre):	shadow-utils, iptables

%if 0%{?with_transcoding} > 0
BuildRequires:  ffmpeg-devel
Requires(pre):	ffmpeg-libs
%endif

Requires:	nc
# Remain compat with other installations
Provides:	rtpengine = %{version}-%{release}

%description
The Sipwise NGCP rtpengine is a proxy for RTP traffic and other UDP based
media traffic. It's meant to be used with the Kamailio SIP proxy and forms a
drop-in replacement for any of the other available RTP and media proxies.


%package kernel
Summary:	NGCP rtpengine in-kernel packet forwarding
Group:		System Environment/Daemons
BuildRequires:	gcc make redhat-rpm-config iptables-devel
Requires:	iptables iptables-ipv6
Requires:	%{name}%{?_isa} = %{version}-%{release}
Requires: 	%{name}-dkms = %{version}-%{release}

%description kernel
%{summary}.


%package dkms
Summary:	Kernel module for NGCP rtpengine in-kernel packet forwarding
Group:		System Environment/Daemons
BuildArch:	noarch
BuildRequires:	redhat-rpm-config
Requires:	gcc make
Requires(post):	dkms
Requires(preun): dkms

%description dkms
%{summary}.


%if 0%{?with_transcoding} > 0
%package recording
Summary:        NGCP rtpengine recording daemon packet
Group:          System Environment/Daemons
BuildRequires:  gcc make redhat-rpm-config mysql-devel ffmpeg-devel

%description recording
%{summary}.

%endif

# define name rtpengine
# define archname rtpengine

%{!?kversion: %define kversion %(uname -r)}
# hint: this can be overridden with "--define kversion foo" on rpmbuild,
# e.g. --define "kversion 2.6.32-696.23.1.el6.x86_64"

%prep
%setup -q -n %{name}-mr%{version}


%build
%if 0%{?with_transcoding} > 0
cd daemon
RTPENGINE_VERSION="\"%{version}-%{release}\"" make
cd ../iptables-extension
RTPENGINE_VERSION="\"%{version}-%{release}\"" make
cd ../recording-daemon
RTPENGINE_VERSION="\"%{version}-%{release}\"" make
cd ..
%else
cd daemon
RTPENGINE_VERSION="\"%{version}-%{release}\"" make with_transcoding=no
cd ../iptables-extension
RTPENGINE_VERSION="\"%{version}-%{release}\"" make with_transcoding=no
cd ..
%endif

%install
# Install the userspace daemon
install -D -p -m755 daemon/%{name} %{buildroot}%{_sbindir}/%{name}
# Install CLI (command line interface)
install -D -p -m755 utils/%{name}-ctl %{buildroot}%{_sbindir}/%{name}-ctl
# Install recording daemon
%if 0%{?with_transcoding} > 0
install -D -p -m755 recording-daemon/%{name}-recording %{buildroot}%{_sbindir}/%{name}-recording
%endif

## Install the INIT script
%if "%{?_unitdir}" == ""
install -D -p -m755 el/%{name}.init \
	%{buildroot}%{_initrddir}/%{name}
%if 0%{?with_transcoding} > 0
install -D -p -m755 el/%{name}-recording.init \
  %{buildroot}%{_initrddir}/%{name}-recording
%endif
%else
# systemd
install -d %{buildroot}%{_unitdir}
install -Dpm 644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
install -Dpm 644 %{SOURCE2} %{buildroot}%{_tmpfilesdir}/%{name}.conf
install -D -p -m755 %{SOURCE3} %{buildroot}%{_sbindir}/rtpengine-iptables-setup
%if 0%{?with_transcoding} > 0
  install -Dpm 644 %{SOURCE4} %{buildroot}%{_unitdir}/%{name}-recording.service
  install -D -p -m755 %{SOURCE5} %{buildroot}%{_sbindir}/rtpengine-recording-nfs-setup
%endif
%endif

# Install configs
install -D -p -m644 el/%{name}.sysconfig \
	%{buildroot}%{_sysconfdir}/sysconfig/%{name}
%if 0%{?with_transcoding} > 0
install -D -p -m644 el/%{name}-recording.sysconfig \
	%{buildroot}%{_sysconfdir}/sysconfig/%{name}-recording
%endif

mkdir -p %{buildroot}%{_sharedstatedir}/%{name}
mkdir -p %{buildroot}%{_var}/spool/%{name}


# Install config files
install -D -p -m644 etc/%{name}.sample.conf \
	%{buildroot}%{_sysconfdir}/%{name}/%{name}.conf
%if 0%{?with_transcoding} > 0
install -D -p -m644 etc/%{name}-recording.sample.conf \
	%{buildroot}%{_sysconfdir}/%{name}/%{name}-recording.conf
%endif

# Install the iptables plugin
install -D -p -m755 iptables-extension/libxt_RTPENGINE.so \
	%{buildroot}/%{_lib}/xtables/libxt_RTPENGINE.so

## DKMS module source install
install -D -p -m644 kernel-module/Makefile \
	 %{buildroot}%{_usrsrc}/%{name}-%{version}-%{release}/Makefile
install -D -p -m644 kernel-module/xt_RTPENGINE.c \
	 %{buildroot}%{_usrsrc}/%{name}-%{version}-%{release}/xt_RTPENGINE.c
install -D -p -m644 kernel-module/xt_RTPENGINE.h \
	 %{buildroot}%{_usrsrc}/%{name}-%{version}-%{release}/xt_RTPENGINE.h
mkdir -p %{buildroot}%{_usrsrc}/%{name}-%{version}-%{release}
install -D -p -m644 kernel-module/rtpengine_config.h \
	 %{buildroot}%{_usrsrc}/%{name}-%{version}-%{release}/rtpengine_config.h
install -D -p -m644 debian/dkms.conf.in %{buildroot}%{_usrsrc}/%{name}-%{version}-%{release}/dkms.conf
sed -i -e "s/__VERSION__/%{version}-%{release}/g" %{buildroot}%{_usrsrc}/%{name}-%{version}-%{release}/dkms.conf

# For RHEL 7, load the compiled kernel module on boot.
%if 0%{?rhel} == 7
  install -D -p -m644 kernel-module/xt_RTPENGINE.modules.load.d \
           %{buildroot}%{_sysconfdir}/modules-load.d/xt_RTPENGINE.conf
%endif

%pre
getent group %{name} >/dev/null || /usr/sbin/groupadd -r %{name}
getent passwd %{name} >/dev/null || /usr/sbin/useradd -r -g %{name} \
	-s /sbin/nologin -c "%{name} daemon" -d %{_sharedstatedir}/%{name} %{name}


%post
%if "%{?_unitdir}" == ""
/sbin/chkconfig --add %{name}
%else
%tmpfiles_create %{name}.conf
/usr/bin/systemctl -q enable %{name}.service
%endif

%post dkms
# Add to DKMS registry, build, and install module
dkms add -m %{name} -v %{version}-%{release} --rpm_safe_upgrade &&
dkms build -m %{name} -v %{version}-%{release} -k %{kversion} --rpm_safe_upgrade &&
dkms install -m %{name} -v %{version}-%{release} -k %{kversion} --rpm_safe_upgrade --force
true


%preun
if [ $1 = 0 ]; then
%if "%{?_unitdir}" == ""
    /sbin/service %{name} stop > /dev/null 2>&1
    /sbin/chkconfig --del %{name}
%else
    %{?systemd_preun %{name}.service}
%endif
fi

%preun dkms
# Remove from DKMS registry
dkms remove -m %{name} -v %{version}-%{release} --rpm_safe_upgrade --all
true

%if "%{?_unitdir}" == ""
%postun
%{?systemd_postun %{name}.service}
%endif

%files
# Userspace daemon
%{_sbindir}/%{name}
# CLI (command line interface)
%{_sbindir}/%{name}-ctl
# init.d script and configuration file
%if "%{?_unitdir}" == ""
%{_initrddir}/%{name}
%else
%{_unitdir}/%{name}.service
%{_tmpfilesdir}/%{name}.conf
%{_sbindir}/rtpengine-iptables-setup
%endif
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%attr(0750,%{name},%{name}) %dir %{_sharedstatedir}/%{name}
# default config
%{_sysconfdir}/%{name}/%{name}.conf
# Documentation
%doc LICENSE README.md el/README.el.md debian/changelog debian/copyright


%files kernel
/%{_lib}/xtables/libxt_RTPENGINE.so


%files dkms
%{_usrsrc}/%{name}-%{version}-%{release}/
%if 0%{?rhel} == 7
  %{_sysconfdir}/modules-load.d/xt_RTPENGINE.conf
%endif


%if 0%{?with_transcoding} > 0
%files recording
# Recording daemon
%{_sbindir}/%{name}-recording
# Init script
%if "%{?_unitdir}" == ""
%{_initrddir}/%{name}-recording
%else
%{_unitdir}/%{name}-recording.service
%{_sbindir}/rtpengine-recording-nfs-setup
%endif

# Sysconfig
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}-recording
# Default config
%{_sysconfdir}/%{name}/%{name}-recording.conf
# spool directory
%attr(0750,%{name},%{name}) %dir %{_var}/spool/%{name}
%endif

%changelog
* Thu Nov 8 2018 Oleh Horbachov <gorbyo@gmail.com> - 6.4.2.1-1
  - update to ngcp-rtpengine version 6.4.2.1
  - refactored for run via systemd
* Wed Oct 24 2018 Oleh Horbachov <gorbyo@gmail.com> - 6.4.1.1-2
  - update to ngcp-rtpengine version 6.4.1.1
  - enable bcg729
* Tue Jul 10 2018 netaskd <netaskd@gmail.com> - 6.4.0.0-1
  - update to ngcp-rtpengine version 6.4.0.0
  - add packet recording
* Thu Nov 24 2016 Marcel Weinberg <marcel@ng-voice.com>
  - Updated to ngcp-rtpengine version 4.5.0 and CentOS 7.2
  - created a new variable "name" to use rtpengine as name for the binaries
    (still using ngcp-rtpenginge as name of the package and daemon - aligned to the .deb packages)
  - fixed dependencies
* Mon Nov 11 2013 Peter Dunkley <peter.dunkley@crocodilertc.net>
  - Updated version to 2.3.2
  - Set license to GPLv3
* Thu Aug 15 2013 Peter Dunkley <peter.dunkley@crocodilertc.net>
  - init.d scripts and configuration file
* Wed Aug 14 2013 Peter Dunkley <peter.dunkley@crocodilertc.net>
  - First version of .spec file
  - Builds and installs userspace daemon (but no init.d scripts etc yet)
  - Builds and installs the iptables plugin
  - DKMS package for the kernel module
