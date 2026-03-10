@echo off
setlocal

set DIR=%~dp0
set CLASSPATH=%DIR%gradle\wrapper\gradle-wrapper.jar;%DIR%gradle\wrapper\gradle-wrapper-shared.jar;%DIR%gradle\wrapper\gradle-cli.jar

set JAVA_EXE=java
if not "%JAVA_HOME%"=="" (
  if exist "%JAVA_HOME%\bin\java.exe" (
    set JAVA_EXE=%JAVA_HOME%\bin\java.exe
  )
)

"%JAVA_EXE%" -Dfile.encoding=UTF-8 -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %*
