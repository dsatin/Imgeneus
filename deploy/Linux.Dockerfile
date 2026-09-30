FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
ARG SERVER
WORKDIR /source
COPY . .
RUN git apply --no-index deploy/litenetwork-compat.patch
RUN git apply --no-index deploy/sylver-interface-compat.patch
RUN git apply --no-index deploy/sylver-invoker-compat.patch
RUN dotnet run --project deploy/CompatibilityChecks/CompatibilityChecks.csproj -c Release
RUN dotnet publish "src/Imgeneus.${SERVER}/Imgeneus.${SERVER}.csproj" \
    -c Release -p:DefineConstants=SHAIYA_US \
    -o /publish
RUN if [ "$SERVER" = World ]; then cp -a src/Imgeneus.World/config /publish/; fi
RUN cp "src/Imgeneus.${SERVER}/NLog.Config" /publish/

FROM mcr.microsoft.com/dotnet/aspnet:6.0
ARG SERVER
ENV SERVER_DLL=Imgeneus.${SERVER}.dll
WORKDIR /app
COPY --from=build /publish .
ENTRYPOINT ["sh", "-c", "exec dotnet \"$SERVER_DLL\""]
