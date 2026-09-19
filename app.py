import numpy as np, pandas as pd, streamlit as st
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="FunnelIQ",layout="wide")
st.title("FunnelIQ — Marketing Attribution & Funnel ROI")
st.caption("Synthetic multi-touch journey analytics. Attribution is illustrative, not causal.")

@st.cache_data
def make_data():
    rng=np.random.default_rng(42); n=5500
    channels=["paid_social","search","email","referral","organic"]; prob=[.31,.23,.15,.12,.19]
    rows=[]; purchases=[]
    for uid in range(1,n+1):
        k=int(rng.integers(1,6)); touch=rng.choice(channels,k,replace=False,p=prob)
        weights={"paid_social":4.8,"search":7.2,"email":1.1,"referral":1.5,"organic":.3}
        base=pd.Timestamp("2026-01-01")+pd.Timedelta(days=int(rng.integers(0,90)))
        for j,ch in enumerate(touch):
            rows.append([uid,base+pd.Timedelta(hours=j*8),ch,weights[ch]*rng.uniform(.7,1.3)])
        entry=touch[0]
        signup=rng.random()<{"paid_social":.55,"search":.64,"email":.72,"referral":.75,"organic":.58}[entry]
        trial=signup and rng.random()<.66; purchase=trial and rng.random()<.38
        if purchase: purchases.append([uid,round(rng.lognormal(4.3,.45),2)])
    return pd.DataFrame(rows,columns=["user_id","timestamp","channel","cost"]),pd.DataFrame(purchases,columns=["user_id","revenue"])

tp,pu=make_data()
model=st.sidebar.radio("Attribution model",["Last-touch","Linear"])
move=st.sidebar.slider("Reallocation %",0.0,.5,.10,.05)
journey=tp.merge(pu,on="user_id",how="inner").sort_values(["user_id","timestamp"])
if model=="Last-touch":
    credited=journey.groupby("user_id").tail(1).copy()
    credited["attributed_revenue"]=credited["revenue"]
else:
    credited=journey.copy()
    credited["attributed_revenue"]=credited["revenue"]/credited.groupby("user_id").user_id.transform("count")
agg=credited.groupby("channel",as_index=False).agg(revenue=("attributed_revenue","sum"),cost=("cost","sum"),conversions=("user_id","nunique"))
agg["ROI"]=agg.revenue/agg.cost.replace(0,np.nan); agg["CAC"]=agg.cost/agg.conversions.replace(0,np.nan)

funnel=pd.DataFrame({"stage":["visit","signup","trial","purchase"],
                     "users":[tp.user_id.nunique(),int(pu.user_id.nunique()/0.66/0.38),int(pu.user_id.nunique()/0.38),pu.user_id.nunique()]})
funnel.users=funnel.users.clip(upper=tp.user_id.nunique())

c1,c2,c3,c4=st.columns(4)
c1.metric("Total Spend",f"USD {agg.cost.sum():,.0f}")
c2.metric("Revenue",f"USD {agg.revenue.sum():,.0f}")
c3.metric("Blended ROI",f"{agg.revenue.sum()/agg.cost.sum():.2f}x")
c4.metric("Conversions",f"{pu.user_id.nunique():,}")

left,right=st.columns(2)
with left: st.plotly_chart(px.funnel(funnel,x="users",y="stage",title="Funnel"),use_container_width=True)
with right: st.plotly_chart(px.bar(agg,x="channel",y="ROI",title=f"Channel ROI — {model}"),use_container_width=True)

low=agg.loc[agg.ROI.idxmin()]; high=agg.loc[agg.ROI.idxmax()]
shift=low.cost*move; lift=max(0,shift*(high.ROI-low.ROI))
st.info(f"Illustrative reallocation: move {move:.0%} of {low.channel} spend to {high.channel}; estimated incremental revenue USD {lift:,.0f}.")

if st.button("Export Excel Summary"):
    out=Path("funneliq_exec_summary.xlsx")
    with pd.ExcelWriter(out,engine="openpyxl") as w:
        agg.to_excel(w,index=False,sheet_name="Channel ROI")
        funnel.to_excel(w,index=False,sheet_name="Funnel")
    st.success(f"Created {out.name}")
