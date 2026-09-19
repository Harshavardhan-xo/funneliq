import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="FunnelIQ | Growth Analytics", page_icon="◈", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.2rem;max-width:1500px}
.hero{padding:1.2rem 1.4rem;border-radius:18px;background:linear-gradient(135deg,#10172a,#273a72);color:white;margin-bottom:1rem}
.hero h1{margin:0;font-size:2rem}.hero p{margin:.35rem 0 0;color:#dce7ff}
.badge{display:inline-block;background:#7c3aed;color:white;padding:.25rem .6rem;border-radius:999px;font-size:.75rem;font-weight:700}
</style>
""",unsafe_allow_html=True)

@st.cache_data
def generate():
    rng=np.random.default_rng(7); n=50000
    channels=["Paid Social","Search","Email","Referral","Organic"]
    campaigns=[f"CMP-{i:02d}" for i in range(1,31)]
    regions=["India","US","UK","EU","APAC"]; devices=["Mobile","Desktop","Tablet"]
    base_cost={"Paid Social":5.4,"Search":7.8,"Email":1.1,"Referral":1.6,"Organic":.25}
    rows=[]; purchases=[]
    for uid in range(1,n+1):
        k=int(rng.integers(1,6)); touch=rng.choice(channels,k,replace=False,p=[.30,.23,.15,.12,.20])
        ts=pd.Timestamp("2026-01-01")+pd.Timedelta(days=int(rng.integers(0,180)))
        region=rng.choice(regions); device=rng.choice(devices,p=[.58,.38,.04])
        for j,ch in enumerate(touch):
            ts=ts+pd.Timedelta(hours=int(rng.integers(2,30))) if j else ts
            rows.append([uid,ts,ch,rng.choice(campaigns),region,device,base_cost[ch]*rng.uniform(.65,1.35)])
        entry=touch[0]
        signup=rng.random()<{"Paid Social":.47,"Search":.62,"Email":.69,"Referral":.72,"Organic":.53}[entry]
        trial=signup and rng.random()<{"Paid Social":.55,"Search":.68,"Email":.73,"Referral":.71,"Organic":.60}[entry]
        purchase=trial and rng.random()<{"Paid Social":.24,"Search":.34,"Email":.41,"Referral":.37,"Organic":.27}[entry]
        if purchase: purchases.append([uid,round(rng.lognormal(4.4,.42),2)])
    return pd.DataFrame(rows,columns=["user_id","timestamp","channel","campaign_id","region","device","cost"]),pd.DataFrame(purchases,columns=["user_id","revenue"])

tp,pu=generate()

with st.sidebar:
    model_name=st.radio("Attribution model",["Last-touch","Linear","Time-decay"])
    move_pct=st.slider("Budget reallocation",0.0,.40,.10,.05)
    regions=st.multiselect("Region",sorted(tp.region.unique()),default=sorted(tp.region.unique()))
    devices=st.multiselect("Device",sorted(tp.device.unique()),default=sorted(tp.device.unique()))

journey_base=tp.merge(pu,on="user_id",how="inner").sort_values(["user_id","timestamp"])
journey=journey_base[journey_base.region.isin(regions)&journey_base.device.isin(devices)].copy()

def attributed(model):
    x=journey.copy()
    if model=="Last-touch":
        x=x.groupby("user_id",as_index=False).tail(1).copy(); x["credited_revenue"]=x["revenue"]
    elif model=="Linear":
        x["credited_revenue"]=x["revenue"]/x.groupby("user_id").user_id.transform("count")
    else:
        x["touch_age"]=x.groupby("user_id").timestamp.transform(lambda s:(s.max()-s).dt.total_seconds()/86400)
        x["weight"]=np.exp(-.55*x.touch_age); x["weight"]/=x.groupby("user_id").weight.transform("sum")
        x["credited_revenue"]=x["revenue"]*x["weight"]
    out=x.groupby("channel",as_index=False).agg(revenue=("credited_revenue","sum"),cost=("cost","sum"),conversions=("user_id","nunique"))
    out["roi"]=out.revenue/out.cost.replace(0,np.nan); out["cac"]=out.cost/out.conversions.replace(0,np.nan)
    return out

agg=attributed(model_name)

st.markdown('<div class="hero"><span class="badge">GROWTH • MARKETING SCIENCE</span><h1>FunnelIQ — Marketing Attribution & ROI Command Center</h1><p>Multi-touch attribution, journey intelligence and controlled budget-reallocation scenarios across a 50,000-user acquisition portfolio.</p></div>',unsafe_allow_html=True)

c1,c2,c3,c4,c5=st.columns(5)
c1.metric("Marketing Spend",f"USD {agg.cost.sum()/1e6:.2f}M")
c2.metric("Attributed Revenue",f"USD {agg.revenue.sum()/1e6:.2f}M")
c3.metric("Blended ROI",f"{agg.revenue.sum()/agg.cost.sum():.2f}x")
c4.metric("Conversions",f"{agg.conversions.sum():,}")
c5.metric("Blended CAC",f"USD {agg.cost.sum()/max(agg.conversions.sum(),1):,.0f}")
st.caption(f"Data scale: {tp.user_id.nunique():,} users • {len(tp):,} touchpoints • {len(pu):,} purchases")

t1,t2,t3,t4=st.tabs(["Executive Overview","Attribution Lab","Journey Intelligence","Budget Simulator"])
with t1:
    l,r=st.columns(2)
    l.plotly_chart(px.bar(agg,x="channel",y="roi",text_auto=".2f",title=f"ROI by Channel — {model_name}"),use_container_width=True)
    funnel=pd.DataFrame({"stage":["Visit","Signup","Trial","Purchase"],
                         "users":[tp.user_id.nunique(),int(tp.user_id.nunique()*.63),int(tp.user_id.nunique()*.42),pu.user_id.nunique()]})
    r.plotly_chart(px.funnel(funnel,y="stage",x="users",title="Acquisition Funnel"),use_container_width=True)
    reg=journey.groupby("region",as_index=False).agg(revenue=("revenue","sum"),users=("user_id","nunique"))
    reg["revenue_per_user"]=reg.revenue/reg.users
    st.plotly_chart(px.bar(reg,x="region",y="revenue_per_user",title="Revenue per Engaged User by Region"),use_container_width=True)
with t2:
    models=pd.concat([attributed("Last-touch").assign(model="Last-touch"),attributed("Linear").assign(model="Linear"),attributed("Time-decay").assign(model="Time-decay")])
    st.plotly_chart(px.bar(models,x="channel",y="roi",color="model",barmode="group",title="Attribution Model Comparison"),use_container_width=True)
    st.dataframe(models.pivot(index="channel",columns="model",values="revenue").reset_index().round(0),use_container_width=True,hide_index=True)
    st.download_button("Download Channel Attribution CSV",agg.to_csv(index=False).encode(),"funneliq_channel_attribution.csv","text/csv")
with t3:
    paths=(journey.assign(path=journey.groupby("user_id").channel.transform(lambda s:" → ".join(s)))
           .groupby("path",as_index=False).agg(users=("user_id","nunique"),revenue=("revenue","sum"))
           .sort_values("revenue",ascending=False).head(15))
    st.dataframe(paths,use_container_width=True,hide_index=True)
    st.plotly_chart(px.bar(paths.head(10),x="revenue",y="path",orientation="h",title="Top Revenue-Generating Journey Paths"),use_container_width=True)
with t4:
    low=agg.loc[agg.roi.idxmin()]; high=agg.loc[agg.roi.idxmax()]
    shift=float(low.cost*move_pct); lift=max(0,shift*(high.roi-low.roi))
    a,b,c=st.columns(3); a.metric("From",low.channel); b.metric("To",high.channel); c.metric("Illustrative Lift",f"USD {lift:,.0f}")
    sim=pd.DataFrame({"Scenario":["Current","Reallocated"],"Revenue":[agg.revenue.sum(),agg.revenue.sum()+lift],"Spend":[agg.cost.sum(),agg.cost.sum()]})
    sim["ROI"]=sim.Revenue/sim.Spend
    st.plotly_chart(px.bar(sim,x="Scenario",y="ROI",text_auto=".2f",title="ROI Sensitivity"),use_container_width=True)
    st.info("The reallocation panel is a transparent sensitivity analysis based on current modeled ROI, not a causal forecast.")
    if st.button("Prepare Executive Excel Summary"):
        buf=io.BytesIO()
        with pd.ExcelWriter(buf,engine="openpyxl") as w:
            agg.to_excel(w,index=False,sheet_name="Channel ROI"); paths.to_excel(w,index=False,sheet_name="Journey Paths"); sim.to_excel(w,index=False,sheet_name="Scenario")
        st.download_button("Download Excel",buf.getvalue(),"funneliq_exec_summary.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
