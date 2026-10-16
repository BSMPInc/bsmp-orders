# Offline copy of apar.html for clicking through the Cash Flow "sum together" bar.
# Firebase is stubbed (fake signed-in manager, fixture accounts + bills, writes are no-ops).
# Run, then open http://localhost:8123/_cashseltest.html; delete _cashseltest.html when done.
import io, re
src = io.open('C:/Users/info/bsmp-orders/apar.html', encoding='utf-8').read()
stub = u'''
const FIX={
  'apar/accounts':{acc_op:{name:'Operating',balance:20000,balanceUpdatedAt:Date.now()},acc_pay:{name:'Payroll',balance:9000,balanceUpdatedAt:Date.now()}},
  'apar/entries':{
    m1:{manual:true,type:'ap',party:'Metal Supply',ref:'MS-1',amount:1000,issue:'2026-10-01',dueDate:'2026-10-30',account:'acc_op',payStatus:'scheduled',planDate:'2026-10-20'},
    m2:{manual:true,type:'ap',party:'Paint Pros',ref:'PP-7',amount:250.50,issue:'2026-10-01',dueDate:'2026-10-25',account:'acc_op',payStatus:'open'},
    m3:{manual:true,type:'ap',party:'Laser LLC',ref:'L-3',amount:400,issue:'2026-10-01',dueDate:'2026-10-22',account:'acc_op',payStatus:'open',payments:[{amount:100,date:'2026-10-05'}]},
    m4:{manual:true,type:'ap',party:'ADP',ref:'Run 20',amount:5000,issue:'2026-10-01',dueDate:'2026-10-18',account:'acc_pay',payStatus:'scheduled'},
    m5:{manual:true,type:'ap',party:'Gas Co',ref:'G-1',amount:75.25,issue:'2026-10-01',dueDate:'2026-10-28',payStatus:'open'}
  }
};
const initializeApp=()=>({}), getDatabase=()=>({}), getAuth=()=>({});
const ref=(db,p)=>p;
const onValue=(p,cb)=>{ setTimeout(()=>cb({val:()=>FIX[p]===undefined?(p==='.info/connected'?true:null):FIX[p]}),0); };
const set=()=>Promise.resolve(), remove=()=>Promise.resolve(), update=()=>Promise.resolve();
const signInWithEmailAndPassword=()=>Promise.resolve(), signOut=()=>Promise.resolve();
const setPersistence=()=>Promise.resolve(), browserLocalPersistence={};
const onAuthStateChanged=(a,cb)=>setTimeout(()=>{ cb({email:'ofc.test@bertsmp.com',displayName:'Test'}); setTimeout(()=>{ try{ page='cash'; render(); }catch(e){ console.error(e); } },50); },0);
'''
src = re.sub(r"import \{[^}]*\} from 'https://www\.gstatic\.com/firebasejs/[^']+';\n", '', src)
src = src.replace("// Same project/login as the order tracker", stub + "\n// Same project/login as the order tracker", 1)
io.open('C:/Users/info/bsmp-orders/_cashseltest.html', 'w', encoding='utf-8', newline='').write(src)
print('wrote _cashseltest.html')
